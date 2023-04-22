import socket
import time

from utils import Message_Type
from utils.messages.voter_messages import Voter_Registration_Message, Voter_Heartbeat_Message

class Client:
    def __init__(self, id):
        # self.voting_vector = {
        #     "What is the best CS class?": ["240", "555", "511"],
        #     "What is the hardest homework in CSCI 55500?": ["H1", "H2", "H3"],
        #     "Who is the best professor in the CS department?": ["Xzou", "Kelly", "Andy"]
        # } 
        self.server = socket.gethostbyname('localhost')
        self.header = 64
        self.format = 'utf-8'
        self.length = 1000
        self.id = id
        self.sock = None
    
    def start(self, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.server, int(port)))

    def send_message(self, message):
        time.sleep(0.1)
        self.sock.sendall(message)
    
    def get_shares(self):
        share = 0
        share_prime = 0
        self.send_message('give me shares')
        message_from_server = self.sock.recv(self.header).decode(self.format)
        share = int(message_from_server.split(',')[0])
        share_prime = int(message_from_server.split(',')[1])
        return [share, share_prime]

    def close_connection(self):
        disconnect_message = Message_Type.MESSAGE.DISCONNECT.value.to_bytes(1, byteorder='big')
        self.send_message(disconnect_message)
        time.sleep(0.1)
        self.sock.close()
        print('Connection closed.')

    def receive_message(self):
        timeout = 10
        self.sock.settimeout(timeout)
        try:
            message = self.sock.recv(int(self.length))
            while message == b'':
                message = self.sock.recv(int(self.length))
        except:
            print(f'No message received within {timeout} seconds, trying again...')
            voter_heartbeat_message = Voter_Heartbeat_Message()
            self.send_message(voter_heartbeat_message.to_bytes())
            self.receive_message()
        message_type = int.from_bytes(message.split(b',')[0], byteorder='big')
        # receive collectors information from the admin
        if message_type == Message_Type.MESSAGE.METADATA_VOTER.value:
            print(f'Received collectors information')
            self.extract_message(message)
            self.connect_with_collectors()
        if message_type == Message_Type.MESSAGE.VOTER_LOCATION.value:
            print(f'GOT MESSAGE FROM COLLECTOR YAY')
        return message
    
    def extract_message(self, message):
        message_parts = message.split(b',')
        self.election_id = message_parts[1].decode()
        self.c1_host = message_parts[3].decode()
        self.c1_port = int.from_bytes(message_parts[4], byteorder='big')
        self.c1_pk_length = message_parts[5].decode()
        self.c1_pk= message_parts[6].decode()
        self.c2_host = message_parts[8].decode()
        self.c2_port = int.from_bytes(message_parts[9], byteorder='big')
        self.c2_pk_length = message_parts[10].decode()
        self.c2_pk = message_parts[11].decode()
        self.m = message_parts[12].decode()

    def connect_with_collectors(self):
        print(f'\nEstablishing a connection with collector 2 and sending it registration request')
        self.start(self.c2_port)
        message = Voter_Registration_Message(self.id)
        self.send_message(message.to_bytes())
        self.receive_message()

    def start_voting(self):
        print(list(self.voting_vector.keys())[0])
        print(list(self.voting_vector.values())[0])
        q1_answer = input("")
        if q1_answer not in list(self.voting_vector.values())[0]:
            raise Exception("Answer is not in the list")
        print(list(self.voting_vector.keys())[1])
        print(list(self.voting_vector.values())[1])
        q2_answer = input("")
        if q2_answer not in list(self.voting_vector.values())[1]:
            raise Exception("Answer is not in the list")
        print(list(self.voting_vector.keys())[2])
        print(list(self.voting_vector.values())[2])
        q3_answer = input("")
        if q3_answer not in list(self.voting_vector.values())[2]:
            raise Exception("Answer is not in the list")
        return q1_answer + "," + q2_answer + "," + q3_answer
    
    def generate_voting_vector(self, vote):
        vector = '000000000'
        voting_list = []
        for i in range(len(list(self.voting_vector.keys()))):
            q_vote = vote.split(',')[i]
            q = list(self.voting_vector.values())[i]
            answer_index = q.index(q_vote) + (3 * self.location)
            vector_list = list(vector)
            vector_list[answer_index] = '1'
            new_vector = ''.join(vector_list)
            v = int(new_vector, 2)
            v_prime = int(new_vector[::-1], 2)
            voting_list.append([v, v_prime]) 
        return voting_list
    
    def generate_all_ballots(self, vote, shares):
        ballots = self.generate_ballots(vote[0], shares[0])
        ballots_prime = self.generate_ballots(vote[1], shares[1])
        return [ballots, ballots_prime]

    def generate_ballots(self, vote, shares):
        return vote + sum(shares)