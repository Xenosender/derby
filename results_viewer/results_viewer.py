import json
import cv2


def create_movie_from_result_file(video_file, result_file, output_video_file):
    with open(result_file) as f:
        results = json.load(f)
        frames_results = results["frames"]

    cap = cv2.VideoCapture(video_file)

    out_video = cv2.VideoWriter(output_video_file,
                                cv2.VideoWriter_fourcc(*'MP4V'),
                                cap.get(cv2.CAP_PROP_FPS),
                                (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))

    current_frame_ind = 0

    while True:
        if not frames_results:
            break

        r, img = cap.read()
        if not r:
            break

        current_frame_ind += 1
        while frames_results and frames_results[0]["frame_index"] < current_frame_ind:
            frames_results.pop(0)
        if not frames_results or frames_results[0]["frame_index"] > current_frame_ind:
            continue

        im_height, im_width, _ = img.shape
        frame_values = frames_results[0]
        out_img = img.copy()
        for key in frame_values:
            if key.lower() in ["human", "face"]:
                for box, score in zip(frame_values[key]["boxes"], frame_values[key]["scores"]):
                    cv2.rectangle(out_img,
                                  (int(box[1] * im_width), int(box[0] * im_height)),
                                  (int(box[3] * im_width), int(box[2] * im_height)),
                                  (255, 0, 0), 2)
                    cv2.putText(out_img,
                                "{:.2f}".format(score),
                                (int(box[1] * im_width) + 2, int(box[0] * im_height) + 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.2, (0, 0, 255), 1, cv2.LINE_4)

        out_video.write(out_img)
        # cv2.imwrite('test.jpg', out_img)

    out_video.release()


if __name__ == "__main__":
    input_file = "/home/cyril/PycharmProjects/Derby/human_detector/example/derby_testmatch_1_firstjam.mp4"
    result_file = "/home/cyril/PycharmProjects/Derby/human_detector/test.json"
    out_file = "/home/cyril/PycharmProjects/Derby/results_viewer/test.mp4"

    create_movie_from_result_file(input_file, result_file, out_file)
