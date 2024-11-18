import json
import os.path
import ffmpeg
import requests
import time
import random

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd", "accept-language": "zh-CN,zh;q=0.9",
    "cookie": "你的cookie",
    "priority": "u=0, i",
    "referer": "https://appezrn4igg1968.h5.xiaoeknow.com/p/course/ecourse/course_2hrBH6JXlSOjkpCwCMxnqj6g9U4?l_program=xe_know_pc",
    "sec-ch-ua": "\"Chromium\";v=\"130\", \"Google Chrome\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": "\"Windows\"", "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate", "sec-fetch-site": "same-origin", "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"}
session = requests.session()
session.headers = headers

# https://appezrn4igg1968.h5.xiaoeknow.com/xe.course.business.video.detail_info.get/2.0.0
"""
bizData[resource_id]: v_666d104be4b0694c98289082
bizData[product_id]: course_2hrBH6JXlSOjkpCwCMxnqj6g9U4
bizData[opr_sys]: Win32
"""


def get_video_info(resource_id):
    data = {
        "bizData[resource_id]": resource_id,
        "bizData[product_id]": "course_2hrBH6JXlSOjkpCwCMxnqj6g9U4",
        "bizData[opr_sys]": "Win32"
    }
    resp = session.post("https://appezrn4igg1968.h5.xiaoeknow.com/xe.course.business.video.detail_info.get/2.0.0",
                        data=data)
    print(resp.json())
    """
    {'code': 0, 'msg': 'success', 'data': {'config_data': {'2': {'config_name': '防拖拽', 'is_open': 0, 'config_type': 2}, '1': {'config_name': '跑马灯', 'is_open': 1, 'config_type': 1}}, 'video_urls': 'W$siZGVmaW5pdGlvbl9uYW@lIjoiXHU5YWQ%XHU#ZTA@IiwiZGVmaW5pdGlvbl9wIjoiNzIwUCIsInVybCI6Imh0dHBzOlwvXC9#LXZvZC@rLnhpYW9la#5vdy5jb#@cL#E%MzA$ZTM#ZjdhNjRhZWVhZTA%NmNjMTU$YmIzNTZiXC9hcHBlenJuNGlnZzE5NjhcL$ZpZGVvXC9iX$VfY$BscjZmMzN#dG8@bWhnN#dkb#dcL#x%ZmwxNHlvMGtwNFwvZHJtXC9tYWluLm0zdTg/c#lnbj@hYzdhNzBjMWRhMjBmNzljMmNmYWRhZGI$Njg%ZmZlYSZ0PTY$MzEwM#VhJnVzPXFrVkJMQ$dTT@UiLCJpc@9zdXBwb$J0IjpmYWxzZSwiZXh0Ijp7Imhvc$QiOiJodHRwczpcL@wvdi@#b#Qtay5%aWFvZWtub$cuY#9tIiwicGF0aCI6ImE%MzA$ZTM#ZjdhNjRhZWVhZTA%NmNjMTU$YmIzNTZiXC9hcHBlenJuNGlnZzE5NjhcL$ZpZGVvXC9iX$VfY$BscjZmMzN#dG8@bWhnN#dkb#dcL#x%ZmwxNHlvMGtwNFwvZHJtIiwicGFyYW0iOiJzaWduPWFjN#E$MGMxZGEyMGY$OWMyY#ZhZGFkYjc#ODhmZmVhJnQ9NjczMTAzZWEmdXM9cWtWQkxDd@NPVSJ9fV0=__ba', 'only_h5_play': 0, 'jump_h5_url': '', 'jump_mini_program_url': 'https://wechatapppro-1252524126.cos.ap-shanghai.myqcloud.com/appezrn4igg1968_v_666d104be4b0694c98289082_qr_code.jpg', 'payment_url': '', 'video_player_type': 0, 'is_auto_play': 1, 'is_try': 0, 'product_try_info': {}, 'last_study_time': 342, 'user_last_process_time': '2024-11-10 15:02:48', 'user_last_process': 100, 'video_info': {'app_id': 'appezrn4igg1968', 'resource_id': 'v_666d104be4b0694c98289082', 'video_length': 342, 'file_name': '1.项目业务介绍.mp4', 'video_audio_url': 'https://v-vod-k.xiaoeknow.com/cf91efe589a64c529f999483f26cf034/appezrn4igg1968/video/b_u_cplr6f33vto5mhg7gdog/lxfl14yo0kp4/main.mp3?sign=0d83180955a8ae02eb598fbc8f80930d&t=673103ea&us=xSyMlzbqts', 'patch_img_url': 'https://commonresource-1252524126.cdn.xiaoeknow.com/image/liye7aqe0yfc.png', 'patch_img_url_compressed': 'https://commonresource-1252524126.cdn.xiaoeknow.com/image/liye7aqe0yfc.png', 'can_select': 1, 'is_drm': 1, 'is_transcode': 1, 'material_app_id': 'appezrn4igg1968', 'play_sign': 'hH7s4v-U-StBTFLEreZ8j1o1sfx1tEUbtVqAM85rFXZP7ruzaTttJ2d9Ntll5aWV0gsX-WFqQFCiBybDvp52oKtktDKl7hdR-E7HTsHq_c8', 'is_report_video_status': True, 'resource_type': 3}}, 'forward_url': ''}
    """
    return resp.json()['data']['video_info']['play_sign'], resp.json()['data']['video_info']['file_name']
    pass


# https://appezrn4igg1968.h5.xiaoeknow.com/xe.material-center.play/getPlayUrl
"""
{
    "org_app_id": "appezrn4igg1968",
    "app_id": "appezrn4igg1968",
    "user_id": "u_66c223e1a129f_8aW32VEFrt",
    "play_sign": [
        "hH7s4v-U-StBTFLEreZ8j1o1sfx1tEUbtVqAM85rFXY_Wvwf_qeinrStwYph_y7w50sEExlV7PXkUMNqv9FvbgPlrWxgrycdz2OMBG03PWs"
    ],
    "play_line": "A",
    "opr_sys": "Win32"
}
"""


def get_play_url(play_sign):
    data = {
        "org_app_id": "appezrn4igg1968",
        "app_id": "appezrn4igg1968",
        "user_id": "u_66c223e1a129f_8aW32VEFrt",
        "play_sign": [
            play_sign
        ],
        "play_line": "A",
        "opr_sys": "Win32"
    }
    resp = session.post("https://appezrn4igg1968.h5.xiaoeknow.com/xe.material-center.play/getPlayUrl",
                        data=json.dumps(data))
    print(resp.json())
    print(resp.json()['data'][play_sign]['play_list']['720p_hls']['play_url'])
    return resp.json()['data'][play_sign]['play_list']['720p_hls']['play_url']
    pass


def download_url(url, dir, file_name):
    if not os.path.exists(dir):
        os.makedirs(dir)
    file_path = os.path.join(dir, file_name)
    if os.path.exists(file_path):
        print(f"{file_path} 已存在，跳过下载")
        return
    ffmpeg.input(url).output(file_path).run()
    pass


def get_cate_list(p_id="0"):
    data = {
        "bizData[app_id]": "appezrn4igg1968",
        "bizData[resource_id]": "v_666d104be4b0694c98289082",
        "bizData[course_id]": "course_2hrBH6JXlSOjkpCwCMxnqj6g9U4",
        "bizData[p_id]": p_id,
        "bizData[order]": "asc",
        "bizData[page]": "1",
        "bizData[page_size]": "50",
        "bizData[sub_course_id]": "subcourse_2hrsJ2rSc3xoRKWwVHClXrECQr9"
    }
    resp = session.post("https://appezrn4igg1968.h5.xiaoeknow.com/xe.course.business.avoidlogin.e_course.resource_catalog_list.get/1.0.0", data=data)
    print(resp.json()['data']['list'])
    return resp.json()['data']['list']
    pass


if __name__ == '__main__':
    top_list = get_cate_list()
    for cate in top_list:
        print(cate['chapter_title'])
        if cate['resource_type'] == 1:
            print(f"{cate['chapter_title']} -> 不是视频分类，跳过！")
            continue
        sub_list = get_cate_list(p_id=cate['chapter_id'])
        for sub_cate in sub_list:
            print(sub_cate['chapter_title'])
            play_sign, file_name = get_video_info(sub_cate['resource_id'])
            url = get_play_url(play_sign)
            download_url(url, 'videos/' + cate['chapter_title'], file_name)
            time.sleep(random.randint(1, 5))
    pass
