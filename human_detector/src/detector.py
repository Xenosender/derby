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

import importlib
from utils import camelcase_to_underscores


class Detector(object):

    def __init__(self, detected_category):
        """
        This class is a base class for all object detectors in single images

        IMPORTANT: all subclasses must be in a module which name is the name of the class but in underscore notation (eg HumanDetector in human_detector.py)
        This allows the factory to dynamically load subclasses.

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
        factory to get detectors. It will convert the name of the class to underscores and try to load a module of this name.

        :param detector_name: str - subclass name to instanciate
        :return: subclass
        """
        filename = camelcase_to_underscores(detector_name)
        module = importlib.import_module(filename)

        for c in Detector.__subclasses__():
            if c.__name__ == detector_name:
                return c
        raise ValueError('Subclass {} not found'.format(detector_name))
