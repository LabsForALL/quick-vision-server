import socket
import zlib

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

    def show_info(self):
        print("Time stamp: " + str(self.time_stamp))
        print("Packet number: " + str(self.packet_number))
        print("Packet count: " + str(self.packet_sum))
        print("Data: " + str(self.img_data))


class PacketsManager:
    packets = {}
    frames = {}

    def add_packet(self, data):
        packet = Packet(data)
        ts = packet.time_stamp

        if ts in packets:
            packets[ts].append(packet)
            if len(packets[ts]) == packet.packet_sum:
                self.create_frame(packets[ts])
        else:
            packets[ts] = [packet]

    def create_frame(self, packets):
        pks = sorted(packets, key=lambda x: x.packet_number)
        img_data = bytearray()
        i = 0
        while i < len(pks):
            img_data.extend(pks[i].img_data)
            i += 1
        jpeg_data = zlib.decompress(img_data)
        with open('picture_out.jpg', 'wb') as f:
            f.write(jpeg_data)


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
packets_manager = PacketsManager()
packets = {}

sock.bind(("", 10000))
print("server started!")


while True:
    data, address = sock.recvfrom(496) # buffer size is 1024 bytes
    packets_manager.add_packet(data)

    print(address)
