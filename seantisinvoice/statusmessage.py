from qc.statusmessage.message import Message

def show(request, msg, msg_type='notice'):
    msg = Message(msg, msg_type=msg_type)
    request.environ['qc.statusmessage'].append(msg)
    
def messages(request):
    msgs = []
    while len(request.environ['qc.statusmessage']):
        msgs.append(request.environ['qc.statusmessage'].pop())
    return msgs