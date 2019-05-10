import importlib
from utils import camelcase_to_underscores


class Detector(object):

    def __init__(self, detected_category):
        """
        This class is a base class for all object detectors in single images

        :param detected_category: str (name of detected object)
        """
        self.detected_category = detected_category
        self.batch_max_size = 1

    def analyze_image(self, image):
        """
        entry point to analyze 1 image (3D nd array, HxWxC)

        :param image: 3D nd array, HxWxC
        :return: dict {"boxes": [...], "scores": [...]} where
                    - boxes : list of [top_left.y, top_left.x, bottom_right.y, bottom_right.x] (with X is horizontal and Y is vertical, openCV)
                    - scores : list of float
        """
        raise NotImplementedError("Detector.analyze_image must be implemented in subclasses")

    def analyze_images(self, images):
        """
        entry point to analyze several images (list of 3D nd array, HxWxC)
        if more images than batch_max_size, only the batch_max_size images will be processed

        :param images: list of 3D nd array, HxWxC
        :return: list of dict {"boxes": [...], "scores": [...]} where
                    - boxes : list of [top_left.y, top_left.x, bottom_right.y, bottom_right.x] (with X is horizontal and Y is vertical, openCV)
                    - scores : list of float
        """
        raise NotImplementedError("Detector.analyze_images must be implemented in subclasses")

    def close(self):
        """
        Method to release all resources
        """
        raise NotImplementedError("Detector.analyze_images must be implemented in subclasses")


class DetectorFactory:

    @staticmethod
    def get_detector(detector_name):
        """
        factory to get detectors

        :param detector_name: str - subclass name to instanciate
        :return: subclass
        """
        filename = camelcase_to_underscores(detector_name)
        module = importlib.import_module(filename)

        for c in Detector.__subclasses__():
            if c.__name__ == detector_name:
                return c
        raise ValueError('Subclass {} not found'.format(detector_name))
