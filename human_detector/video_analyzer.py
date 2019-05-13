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
import sys

from detector import DetectorFactory

logging.basicConfig(stream=sys.stdout,
                    level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class VideoAnalyzer(object):

    def __init__(self, frame_ratio=1.):
        self._logger = logging.getLogger("VideoAnalyzer")
        self._logger.info("Creating Video Analyzer")
        self._detectors_names = ["HumanDetector"]
        self._detectors = []
        for n in self._detectors_names:
            self._logger.info('Instantiating detector {}'.format(n))
            self._detectors.append(DetectorFactory.get_detector(n)())

        self._analysis_ratio = frame_ratio

    def analyze_video(self, path_to_video):
        one_frame_every_n_frame = int(1./self._analysis_ratio)
        self._logger.info("Analyzing file {}, 1 frame every {} frame".format(path_to_video, one_frame_every_n_frame))
        cap = cv2.VideoCapture(path_to_video)

        vid_fps = cap.get(cv2.CAP_PROP_FPS)
        vid_codec_code = cap.get(cv2.CAP_PROP_FOURCC)
        self._logger.info("Detected codec and FPS: {}, {}".format(vid_codec_code, vid_fps))

        max_batch_size = min([c.batch_max_size for c in self._detectors])
        current_frame_ind = 0
        input_timestamps = []
        input_images = []
        frame_results = []

        def process_results(frames_info, results_dict):
            results = []
            for i, (f_ind, f_tsp) in enumerate(frames_info):
                im_res = {
                    "frame_index": f_ind,
                    "frame_timestamp": f_tsp
                }
                for key in results_dict:
                    im_res[key] = results_dict[key][i]
                results.append(im_res)
            return results

        while True:
            r, img = cap.read()
            if not r:
                break

            current_frame_ind += 1
            if (current_frame_ind - 1) % one_frame_every_n_frame != 0:
                continue

            if len(input_images) < max_batch_size:
                input_images.append(img)
                input_timestamps.append((current_frame_ind, cap.get(cv2.CAP_PROP_POS_MSEC)))

            if len(input_images) == max_batch_size:
                detection_results = {}
                for det in self._detectors:
                    det_results = det.analyze_images(input_images)
                    detection_results[det.detected_category] = det_results
                batch_results = process_results(input_timestamps, detection_results)
                frame_results.extend(batch_results)
                input_images = []
                input_timestamps = []

        detection_results = {}
        for det in self._detectors:
            det_results = det.analyze_images(input_images)
            detection_results[det.detected_category] = det_results
        batch_results = process_results(input_timestamps, detection_results)
        frame_results.extend(batch_results)

        cap.release()
        self._logger.info("Analyzed {} images".format(len(frame_results)))

        return {"fps": vid_fps, "codec_code": vid_codec_code, "frames": frame_results}

    def close(self):
        self._logger.info("Closing all detectors")
        [c.close() for c in self._detectors]


if __name__ == "__main__":
    import json

    test_video = "example/derby_testmatch_1_firstjam.mp4"

    analyzer = VideoAnalyzer(0.1)
    results = analyzer.analyze_video(test_video)
    with open('test.json', 'w') as f:
        json.dump(results, f)

    analyzer.close()