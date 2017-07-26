import socket
import numpy as np
import tensorflow as tf
import cv2
import json
import base64
import time
from multiprocessing import Process, Queue
from threading import Thread
import packets_manager


class FramesManager:
    last_frame = None
    stopped = False
    queue = None

    def watch_frames(self):
        while not self.stopped:
            self.last_frame = self.queue.get()

    def __init__(self, q):
        self.queue = q
        t = Thread(target=self.watch_frames)
        t.start()
        print('frames manager started')

    def stop(self):
        self.stopped = True


def process_frames(q: Queue):

    stopped = False

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

    # starting OpenCV window thread
    window_title = 'preview'
    cv2.startWindowThread()
    cv2.namedWindow(window_title)

    fm = FramesManager(q)

    while not stopped:

        if fm.last_frame:

            t1 = time.time()

            # processing with the neural network
            input_instance = dict(input=base64.urlsafe_b64encode(fm.last_frame).decode("ascii"), key="0")
            input_instance = json.loads(json.dumps(input_instance))
            input_value = np.array(input_instance["input"])

            output_value = sess.run(output, feed_dict={input: np.expand_dims(input_value, axis=0)})[0]
            output_instance = dict(output=output_value.decode("ascii"), key="0")
            b64data = output_instance["output"]
            b64data += "=" * (-len(b64data) % 4)
            output_data = base64.urlsafe_b64decode(b64data.encode("ascii"))

            # converting output to OpenCV image
            nparr = np.fromstring(output_data, np.uint8)
            img_np = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
            cv2.imshow(window_title, img_np)

            print("FPS : " + str(1/(time.time() - t1)))


class Server:

    def __init__(self, port):
        # starting UDP server
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.pm = packets_manager.PacketsManager()

    def start(self):
        self.sock.bind(("", self.port))
        print("server started!")

        while True:

            # waiting for packets
            data, address = self.sock.recvfrom(496)  # buffer size is 496 bytes
            self.pm.manage_data(data)
            



if __name__ == '__main__':

    server = Server(10000)
    server.start()

    packets_dic = {}
    queue = Queue()
    p = Process(target=process_frames, args=(queue,))
    p.start()


        # Wait for the worker to finish
        # queue.close()
        # queue.join_thread()
        # p.join()