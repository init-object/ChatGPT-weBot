
group_id_dict= dict()
friend_id_dict= dict()
group_name_dict= dict()
friend_name_dict= dict()

class Group:
    def __init__(self, room_id, room_name):
        self.room_id = room_id
        self.room_name = room_name
    def __str__(self):
        return "group_name: " + self.room_name + "\ngroup_id: \"" + self.room_id + "\"\n"

class Friend:
    def __init__(self, wx_id, wx_name, wx_code):
        self.wx_id = wx_id
        self.wx_name = wx_name
        self.wx_code = wx_code
    def __str__(self):
        return "wx_name: " + self.wx_name + "\nwx_id: \"" + self.wx_id + "\"\n"