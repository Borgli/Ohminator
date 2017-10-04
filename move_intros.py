import os

servers = os.listdir("servers")
for server in servers:
    try:
        members_loc = "servers/{}/members".format(server)
        members = os.listdir(members_loc)
        for member in members:
            if member.isdigit():
                for from_member in members:
                    if from_member.endswith(member) and from_member != member :
                        intro_folder_from = "{}/{}/intros".format(members_loc, from_member)
                        intro_folder_to = "{}/{}/intros".format(members_loc, member)
                        intros = os.listdir(intro_folder_from)
                        for intro in intros:
                            print(from_member, " ", member, " ", intro)
                            src = "{}/{}".format(intro_folder_from, intro)
                            dst = "{}/{}".format(intro_folder_to, intro)
                            print(src, " ", dst)
                            os.rename(src, dst)
    except:
        continue
