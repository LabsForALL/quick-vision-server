import socket
import numpy as np
import tensorflow as tf
import zlib
import cv2
import json
import base64
import time
from multiprocessing import Process, Queue
import threading

class Packet:
    img_data = 0
    time_stamp = 0
    packet_number = 0
    packet_sum = 0

    def __init__(self, data):
        self.time_stamp = int.from_bytes(data[0:8], byteorder='big')
        self.packet_number = int.from_bytes(data[8:12], byteorder='big')
        self.packet_sum = int.from_bytes(data[12:16], byteorder='big')
        self.img_data = data[16:497]


def process_frames(q: Queue):

    stopped = False
    last_frame = None;

    # restoring the exported model
    model_dir = 'exported_model/'
    sess = tf.Session()
    saver = tf.train.import_meta_graph(model_dir + "export.meta")
    saver.restore(sess, model_dir + "export")
    input_vars = json.loads(tf.get_collection("inputs")[0].decode('utf-8'))
    output_vars = json.loads(tf.get_collection("outputs")[0].decode('utf-8'))
    input = tf.get_default_graph().get_tensor_by_name(input_vars["input"])
    output = tf.get_default_graph().get_tensor_by_name(output_vars["output"])
    print("model ready!")

    window_title = 'preview'
    cv2.startWindowThread()
    cv2.namedWindow(window_title)

    while not stopped:

        frame_data = q.get()

        print(frame_data)

        # processing with the neural network
        input_instance = dict(input=base64.urlsafe_b64encode(frame_data).decode("ascii"), key="0")
        input_instance = json.loads(json.dumps(input_instance))
        input_value = np.array(input_instance["input"])

        output_value = sess.run(output, feed_dict={input: np.expand_dims(input_value, axis=0)})[0]
        output_instance = dict(output=output_value.decode("ascii"), key="0")
        b64data = output_instance["output"]
        b64data += "=" * (-len(b64data) % 4)
        output_data = base64.urlsafe_b64decode(b64data.encode("ascii"))
        nparr = np.fromstring(output_data, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        cv2.imshow(window_title, img_np)


if __name__ == '__main__':

    # starting UDP server
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 10000))
    print("server started!")

    packets_dic = {}
    queue = Queue()
    p = Process(target=process_frames, args=(queue,))
    p.start()

    while True:

        # waiting for packets
        ts1 = time.time()
        data, address = sock.recvfrom(496)  # buffer size is 496 bytes
        new_packet = Packet(data)
        new_ts = new_packet.time_stamp

        if new_ts in packets_dic:
            packets_dic[new_ts].append(new_packet)

            # checking if frame is ready
            if len(packets_dic[new_ts]) == new_packet.packet_sum:

                # building the frame from packets
                s_packets = sorted(packets_dic[new_ts], key=lambda x: x.packet_number)
                img_data = bytearray()
                i = 0
                while i < len(s_packets):
                    img_data.extend(s_packets[i].img_data)
                    i += 1

                # i = len(img_data) - 1
                # while True:
                #     if img_data[i] != 0:
                #         break
                #     i -= 1
                # del img_data[i+1:]

                jpeg_data = zlib.decompress(img_data)

                queue.put(jpeg_data)

                # clean up
                del packets_dic[new_ts]

                for packet in packets_dic:
                    if packets_dic[packet].time_stamp < new_ts:
                        del packet
        else:
            packets_dic[new_ts] = [new_packet]

        print('Received packet in ' + str(time.time() - ts1))

    # Wait for the worker to finish
    # queue.close()
    # queue.join_thread()
    # p.join()
