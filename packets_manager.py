import zlib


class Packet:

    def __init__(self, data):
        self.time_stamp = int.from_bytes(data[0:8], byteorder='big')
        self.packet_number = int.from_bytes(data[8:12], byteorder='big')
        self.packet_sum = int.from_bytes(data[12:16], byteorder='big')
        self.img_data = data[16:497]


class Frame:

    def __init__(self, time_stamp, jpg_data):
        self.time_stamp = time_stamp
        self.jpg_data = jpg_data


class PacketsManager:

    def __init__(self):
        self.packets_dic = {}  # timestamps for keys and array of packets for values
        self.recent_frame = Frame(0, None)  # creating fake frame without data for initialization

    def manage_data(self, data):

        # creating new packet from the received data
        packet = Packet(data)

        # dropping the packet if it is from older frame
        if packet.time_stamp < self.recent_frame.time_stamp:
            del packet
            return

        # searching for existing packets array with the same timestamp as key
        if packet.time_stamp in self.packets_dic:

            # appending the new packet to the already available array of packets
            self.packets_dic[packet.time_stamp].append(packet)

            # creating new recent frame if the data is complete
            if len(self.packets_dic[packet.time_stamp]) == packet.packet_sum:
                self.create_new_recent_frame(packet.time_stamp)
                self.clean_old_packets(packet.time_stamp)
        else:
            # creating new key value pair
            self.packets_dic[packet.time_stamp] = [packet]

    def create_new_recent_frame(self, ts):

        # building the frame from the packets array
        s_packets = sorted(self.packets_dic[ts], key=lambda x: x.packet_number)
        img_data = bytearray()
        i = 0
        while i < len(s_packets):
            img_data.extend(s_packets[i].img_data)
            i += 1
        self.recent_frame = Frame(ts, zlib.decompress(img_data))

    def clean_old_packets(self, recent_ts):

        # cleaning everything older or equal to the most recent timestamp
        for key_ts in self.packets_dic:
            if key_ts <= recent_ts:
                del self.packets_dic[key_ts]