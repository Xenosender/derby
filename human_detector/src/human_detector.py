# Copyright 2019 Cyril Poulet, cyril.poulet@centraliens.net
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import cv2
import numpy as np
import tensorflow as tf
import logging
import time
import sys

from utils import get_available_gpus
from detector import Detector

logging.basicConfig(stream=sys.stdout,
                    level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# COCO -> human is cat 1

tf_model = "model/faster_rcnn_resnet101_coco"
tf_model_human_threshold = 0.300000011921
coco_output_ind_for_humans = 1
target_input_width = 1024
batch_max_size = 5


class HumanDetector(Detector):

    def __init__(self,
                 saved_model=tf_model,
                 output_ind_for_humans=coco_output_ind_for_humans,
                 min_detection_score=tf_model_human_threshold,
                 max_batch_size=batch_max_size):
        """
        This class implements a detector of people in images, based on a trained model which is loaded at init.
        Model must be a trained TF model.
        To be able to leverage GPUs (if available), it must be a saved checkpoint (meta/index/data), not a frozen model (pb)

        :param saved_model: path to the model files (no extension)
        :param output_ind_for_humans: index of the output class for humans
        :param min_detection_score: threshold for detection score for class "human"
        """
        super().__init__("Human")
        self._model_file = saved_model
        self._output_ind_for_humans = output_ind_for_humans
        self._min_detection_score = min_detection_score
        self.batch_max_size = max_batch_size

        self._graph = None
        self._tf_sess = None
        self._input_placeholder = None
        self._output_nb_detections = None
        self._output_classes = None
        self._output_boxes = None
        self._output_scores = None

        self._logger = logging.getLogger('HumanDetector')

        try:
            self._load_model()
        except Exception as e:
            self._logger.error("Error loading model : {}".format(e))
            raise e

    def _load_model(self):
        """
        Load model on GPU if available, else on CPU, and get placeholders for input and outputs

        :return: None
        """
        self._logger.info('Loading model...')
        self._logger.debug('creating TF session')
        self._tf_sess = tf.Session(graph=self._graph, config=tf.ConfigProto(allow_soft_placement=True))
        gpus = get_available_gpus()
        if gpus:
            self._logger.debug('loading graph on GPU')
            with tf.device(gpus[0]):
                new_saver = tf.train.import_meta_graph(self._model_file + '.meta', clear_devices=True)
                new_saver.restore(self._tf_sess, self._model_file)
                self._graph = self._tf_sess.graph
        else:
            self._logger.debug('loading graph on CPU')
            new_saver = tf.train.import_meta_graph(self._model_file + '.meta', clear_devices=True)
            new_saver.restore(self._tf_sess, self._model_file)
            self._graph = self._tf_sess.graph

        self._logger.debug('getting placeholders')
        # get graph input placeholder
        self._input_placeholder = self._graph.get_tensor_by_name('image_tensor:0')
        # get output placeholders
        self._output_nb_detections = self._graph.get_tensor_by_name('num_detections:0')
        self._output_classes = self._graph.get_tensor_by_name('detection_classes:0')
        self._output_boxes = self._graph.get_tensor_by_name('detection_boxes:0')
        self._output_scores = self._graph.get_tensor_by_name('detection_scores:0')
        self._logger.info('... model loaded')

    def close(self):
        """
        Close TF session and graph

        :return: None
        """
        self._logger.info('Closing session and graph')
        self._tf_sess.close()

    def analyze_image(self, image):
        """
        entry point to analyze 1 image (3D nd array, HxWxC)

        :param image: 3D nd array, HxWxC
        :return: dict {"classes" : [...], "boxes": [...], "scores": [...]} where
                        - classes = list of int
                        - boxes : list of [top_left.y, top_left.x, bottom_right.y, bottom_right.x] (with X is horizontal and Y is vertical, openCV)
                        - scores : list of float
        """
        preprocessed_input = self._preprocess_image(image)
        model_output = self._run_model([preprocessed_input])[0]
        filtered_output = self._filter_humans(model_output)
        return filtered_output

    def analyze_images(self, images):
        """
        entry point to analyze several images (list of 3D nd array, HxWxC)
        if more images than batch_max_size, only the batch_max_size images will be processed

        :param images: list of 3D nd array, HxWxC
        :return: list of dict {"classes" : [...], "boxes": [...], "scores": [...]} where
                        - classes = list of int
                        - boxes : list of [top_left.y, top_left.x, bottom_right.y, bottom_right.x] (with X is horizontal and Y is vertical, openCV)
                        - scores : list of float
        """
        if len(images) > batch_max_size:
            self._logger.warning('Too much images in HumanDetector.analyze_images. Only the {} will be processed'.format(batch_max_size))
            images = images[:batch_max_size]
        preprocessed_inputs = [self._preprocess_image(im) for im in images]
        model_outputs = self._run_model(preprocessed_inputs)
        filtered_outputs = [self._filter_humans(out) for out in model_outputs]
        return filtered_outputs

    def _preprocess_image(self, input_image):
        """
        resize image to target_input_width while keeping the ratio

        :param input_image: 3D nd array
        :return: 3D nd array
        """
        w = input_image.shape[1]
        ratio = float(target_input_width) / float(w)
        resized_img = cv2.resize(input_image, (target_input_width, int(float(input_image.shape[0])*ratio)))
        return resized_img

    def _run_model(self, input_images):
        """
        run the TF model on list of input images

        :param input_images: list of 3D nd array
        :return: list of dict {"classes" : [...], "boxes": [...], "scores": [...]} where
                        - classes = list of int
                        - boxes : list of [top_left.y, top_left.x, bottom_right.y, bottom_right.x] (with X is horizontal and Y is vertical, openCV)
                        - scores : list of float
        """
        # Expand dimensions since the trained_model expects images to have shape: [1, None, None, 3]
        images_np_expanded = np.vstack([np.expand_dims(im, axis=0) for im in input_images])
        # Actual detection.
        start_time = time.time()
        (num, classes, boxes, scores) = self._tf_sess.run(
            [self._output_nb_detections,
             self._output_classes,
             self._output_boxes,
             self._output_scores],
            feed_dict={self._input_placeholder: images_np_expanded})
        end_time = time.time()
        self._logger.debug("Predicting {} images. Processing Time: {}s".format(len(input_images), end_time - start_time))

        results = []
        for im_ind in range(len(input_images)):
            num_res = int(num[im_ind])
            results.append({"classes": [int(x) for x in classes[im_ind].tolist()][:num_res],
                            "boxes":  boxes[im_ind].tolist()[:num_res],
                            "scores": scores[im_ind].tolist()[:num_res]})

        return results

    def _filter_humans(self, results):
        """
        Filters the predictions for a single image to keep only the humans detected with a score above a given threshold

        :param results: dict {"classes" : [...], "boxes": [...], "scores": [...]} where
                        - classes = list of int
                        - boxes : list of [top_left.y, top_left.x, bottom_right.y, bottom_right.x] (with X is horizontal and Y is vertical, openCV)
                        - scores : list of float
        :return: same as input
        """
        # filter on class
        humans_boxes, humans_scores = [], []
        filtered_tuples = [triplet for triplet in zip(results["classes"], results["boxes"], results["scores"]) if triplet[0] == self._output_ind_for_humans]
        if len(filtered_tuples):
            _, humans_boxes, humans_scores = zip(*filtered_tuples)

        # filter on score
        correct_humans_boxes, correct_humans_scores = [], []
        filtered_tuples = [vals for vals in zip(humans_boxes, humans_scores) if vals[1] >= self._min_detection_score]
        if len(filtered_tuples):
            correct_humans_boxes, correct_humans_scores = zip(*filtered_tuples)

        return {"classes": [self._output_ind_for_humans for _ in correct_humans_scores],
                "boxes": list(correct_humans_boxes),
                "scores": list(correct_humans_scores)}


if __name__ == "__main__":

    my_detector = HumanDetector()

    test_image = cv2.imread("example/test_image_derby.jpg")
    results = my_detector.analyze_images([test_image, test_image])

    im_height, im_width, _ = test_image.shape
    for box in results[0]["boxes"]:
        cv2.rectangle(test_image,
                      (int(box[1] * im_width), int(box[0] * im_height)),
                      (int(box[3] * im_width), int(box[2] * im_height)),
                      (255, 0, 0), 2)

    cv2.imwrite('test.jpg', test_image)

