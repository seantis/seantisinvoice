from qc.statusmessage.message import Message

def show(request, msg, msg_type=u'notice'):
    msg = Message(msg, msg_type=msg_type)
    if 'qc.statusmessage' in request.environ:
        request.environ['qc.statusmessage'].append(msg)
    
def messages(request):
    msgs = []
    if 'qc.statusmessage' in request.environ:
        while len(request.environ['qc.statusmessage']):
            msgs.append(request.environ['qc.statusmessage'].pop())
    return msgs