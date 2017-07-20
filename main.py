import socket
import numpy as np
import zlib
import cv2


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


class PacketsManager:
    packets_dic = {}
    frames = {}

    def add_packet(self, data):
        new_packet = Packet(data)
        new_ts = new_packet.time_stamp

        if new_ts in packets_dic:
            packets_dic[new_ts].append(new_packet)
            if len(packets_dic[new_ts]) == new_packet.packet_sum:
                self.create_frame(packets_dic[new_ts])
                del packets_dic[new_ts]
        else:
            packets_dic[new_ts] = [new_packet]

    def create_frame(self, packets):
        pks = sorted(packets, key=lambda x: x.packet_number)
        img_data = bytearray()
        i = 0
        while i < len(pks):
            img_data.extend(pks[i].img_data)
            i += 1
        jpeg_data = zlib.decompress(img_data)

        nparr = np.fromstring(jpeg_data, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        cv2.imshow(window_title, img_np)


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
packets_manager = PacketsManager()
packets_dic = {}

sock.bind(("", 10000))
print("server started!")

window_title = 'preview'
cv2.startWindowThread()
cv2.namedWindow(window_title)

while True:
    data, address = sock.recvfrom(496) # buffer size is 1024 bytes
    packets_manager.add_packet(data)

    print(address)
