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
import logging
import time
import sys
import numpy as np
import tensorflow as tf

from detector import Detector


logging.basicConfig(stream=sys.stdout,
                    level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


tf_model = "model/mobilenet_SSD_widerface.pb"
tf_model_human_threshold = 0.5
widerface_output_ind_for_humans = 1
target_input_width = 1024
batch_max_size = 5


class FaceDetector(Detector):

    def __init__(self,
                 model_file=tf_model,
                 target_input_width=target_input_width,
                 min_detection_score=tf_model_human_threshold,
                 max_batch_size=batch_max_size):
        """
        This class implements a detector of faces in images, using a mobilenet SingleShot Detector trained on WiderFace database.
        Credits for the trained model to https://github.com/yeephycho/tensorflow-face-detection
        """
        super().__init__("Face")

        self._model_file = model_file
        self._target_input_width = target_input_width
        self._min_detection_score = min_detection_score
        self.batch_max_size = max_batch_size

        self._graph = None
        self._tf_sess = None
        self._input_placeholder = None
        self._output_nb_detections = None
        self._output_classes = None
        self._output_boxes = None
        self._output_scores = None

        self._logger = logging.getLogger('FaceDetector')

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
        self._graph = tf.Graph()
        with self._graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(self._model_file, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

        with self._graph.as_default():
            config = tf.ConfigProto()
            config.gpu_options.allow_growth = True
            self._tf_sess = tf.Session(graph=self._graph, config=config)

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
        filtered_output = self._filter_by_score(model_output)
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
        filtered_outputs = [self._filter_by_score(out) for out in model_outputs]
        return filtered_outputs

    def _preprocess_image(self, input_image):
        """
        resize image to target_input_width while keeping the ratio

        :param input_image: 3D nd array
        :return: 3D nd array
        """
        w = input_image.shape[1]
        ratio = float(self._target_input_width) / float(w)
        resized_img = cv2.resize(input_image, (self._target_input_width, int(float(input_image.shape[0])*ratio)))

        cvt_image = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)
        return cvt_image

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
        self._logger.debug(
            "Predicting {} images. Processing Time: {}s".format(len(input_images), end_time - start_time))

        results = []
        for im_ind in range(len(input_images)):
            num_res = int(num[im_ind])
            results.append({"classes": [int(x) for x in classes[im_ind].tolist()][:num_res],
                            "boxes": boxes[im_ind].tolist()[:num_res],
                            "scores": scores[im_ind].tolist()[:num_res]})
        return results

    def _filter_by_score(self, results):
        """
        Filters the predictions for a single image to keep only the humans detected with a score above a given threshold

        :param results: dict {"classes" : [...], "boxes": [...], "scores": [...]} where
                        - classes = list of int
                        - boxes : list of [top_left.y, top_left.x, bottom_right.y, bottom_right.x] (with X is horizontal and Y is vertical, openCV)
                        - scores : list of float
        :return: same as input
        """
        # filter on score
        correct_faces_boxes, correct_faces_scores = [], []
        filtered_tuples = [vals for vals in zip(results["boxes"], results["scores"]) if vals[1] >= self._min_detection_score]
        if len(filtered_tuples):
            correct_faces_boxes, correct_faces_scores = zip(*filtered_tuples)

        return {"classes": [0 for _ in correct_faces_scores],
                "boxes": list(correct_faces_boxes),
                "scores": list(correct_faces_scores) }


if __name__ == "__main__":

    my_detector = FaceDetector()

    test_image = cv2.imread("example/test_image_derby.jpg")
    results = my_detector.analyze_image(test_image)

    im_height, im_width, _ = test_image.shape
    for box in results["boxes"]:
        cv2.rectangle(test_image,
                      (int(box[1] * im_width), int(box[0] * im_height)),
                      (int(box[3] * im_width), int(box[2] * im_height)),
                      (255, 0, 0), 2)

    cv2.imwrite('test.jpg', test_image)

