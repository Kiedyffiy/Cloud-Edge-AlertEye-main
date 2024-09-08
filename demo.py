import time
import cv2
from rknnlite.api import RKNNLite
import edge
import json
import requests

class edgeAndCloud():
    def __init__(self):
        self.video_path='day_man_001_30_2.mp4'
        self.rknn_model_path='best.rknn'
        self.init_mouth_ro=0.0
        self.init_yaw=0.0
        self.init_pitch=0.0
        self.return_res=[]
        self.time_list=[]
        self.token=''
        self.url='https://48ba86fb27fe4d75a3042ef1e0c9741e.apig.cn-north-4.huaweicloudapis.com/v1/infers/76c89b98-4e51-4a2f-aa72-851d62bbcf12'
        self.words=['','闭眼','哈欠','手机','歪头']
        pass

    def tishi(self,cls):
        # cls对应相应行为状态
        # 1：闭眼
        # 2：哈欠
        # 3：手机
        # 4：歪头
        print(f'结果代号为：{cls} ,行为是：{self.words[cls]}')
        pass

    def finalRes(self):
        # 最后结果
        # 处理return_res
        print(self.return_res)
        pass
    
    def getToken(self,time_out=3):
        # 定义请求头
        headers = {
            'Content-Type': 'application/json'
        }

        # 定义请求体
        data = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "name": "hw60758523",
                            "password": "wqz123456",
                            "domain": {
                                "name": "hw60758523"
                            }
                        }
                    }
                },
                "scope": {
                    "project": {
                        "name": "cn-north-4"
                    }
                }
            }
        }
        try:
            response = requests.post('https://iam.cn-north-4.myhuaweicloud.com/v3/auth/tokens', headers=headers, data=json.dumps(data),timeout=time_out)
            response.raise_for_status()  # 检查响应是否成功
            # 获取X-Subject-Token字段并转为字符串
            self.token = response.headers.get('X-Subject-Token', '')
        except requests.exceptions.Timeout:
            print('超时')
        except requests.exceptions.RequestException as e:
            print(f'请求失败: {e}')

    def sendCloud(self,frame,mouthRo,init_yaw,init_pitch,time_out=3.28):
        float_list=[mouthRo,init_yaw,init_pitch]

        _, img_encode = cv2.imencode('.png', frame)
        img_bytes = img_encode.tobytes()

        headers = {
            'X-Auth-Token': self.token
        }
        files = {
            'images': img_bytes,
            'axis':(None, json.dumps(float_list), 'application/json')
        }
        try:
            resp = requests.post(self.url, headers=headers, files=files,timeout=time_out)
            if resp.status_code!=200:
                print('codeNo200')
                return []
            return json.loads(resp.text).get("res_res", [])
        except requests.exceptions.Timeout:
            print('timeout')
            return []
    
    def load_model(self):
        self.edge_obj_post=edge.edgeSide()

    def get_init_info(self):
        self.init_mouth_ro=1.6
        self.init_yaw=-19.1
        self.init_pitch=-9.2

    def start(self):
        # load RKNN model
        RKNN_MODEL=self.rknn_model_path
        print('--> Load RKNN model')
        rknn = RKNNLite()
        rknn.load_rknn(RKNN_MODEL)
        print('--> Init runtime environment')
        ret = rknn.init_runtime()
        if ret != 0:
            print('Init runtime environment failed!')
            exit(ret)
        print('done')

        # deal frames
        cap = cv2.VideoCapture(self.video_path)

        head_mark, eye_mark, mouth_mark, phone_mark = False, False, False, False
        head_first_idx, eye_first_idx, mouth_first_idx, phone_first_idx = -1, -1, -1, -1
        head_end_idx, eye_end_idx, mouth_end_idx, phone_end_idx = -1, -1, -1, -1

        frame_cnt = -1
        video_fps = int(cap.get(cv2.CAP_PROP_FPS))
        fps = 3
        frames_gap = int(video_fps / fps)

        while (cap.isOpened()):
            frame_cnt += 1
            _,frame = cap.read()
            self.time_list.append(int(cap.get(cv2.CAP_PROP_POS_MSEC)))
            if frame_cnt % frames_gap != 0:
                continue

            end2end_start = time.time()

            h, w, _ = frame.shape
            w_a = int(w * 0.45)
            w_b = int(w * 1)
            frame_afi = frame[0:h, w_a:w_b]
            img = cv2.cvtColor(frame_afi, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (640, 640))

            outputs = rknn.inference(inputs=[img])

            # 并行1
            boxes, res_edge, scores = self.edge_obj_post.yolov5_post_process(outputs)
            # 并行2
            res_cloud=self.sendCloud(frame,self.init_mouth_ro,self.init_yaw,self.init_pitch)
            # 两个res合并
            res=res_cloud.copy()
            for item in res_edge:
                if item not in res:
                    res.append(item)

            i = frame_cnt

            if 3 in res or len(res)==0:
                if head_first_idx==-1:
                    head_first_idx=i
                    head_end_idx=i
                    head_mark=True
                else:
                    head_end_idx=i
            if head_mark and i-head_end_idx>=frames_gap:
                if head_end_idx-head_first_idx>=8*frames_gap:
                    tmp_res={
                        "periods":[self.time_list[head_first_idx],self.time_list[head_end_idx]],
                        "category":4
                    }
                    self.return_res.append(tmp_res)
                    self.tishi(4)
                head_first_idx=-1
                head_mark=False
            
            if 4 in res:
                if mouth_first_idx==-1:
                    mouth_first_idx=i
                    mouth_end_idx=i
                    mouth_mark=True
                else:
                    mouth_end_idx=i
            if mouth_mark and i-mouth_end_idx>=frames_gap:
                if mouth_end_idx-mouth_first_idx>=8*frames_gap:
                    tmp_res={
                        "periods":[self.time_list[mouth_first_idx],self.time_list[mouth_end_idx]],
                        "category":2
                    }
                    self.return_res.append(tmp_res)
                    self.tishi(2)
                mouth_first_idx=-1
                mouth_mark=False
            
            if 0 in res:
                if eye_first_idx==-1:
                    eye_first_idx=i
                    eye_end_idx=i
                    eye_mark=True
                else:
                    eye_end_idx=i
            if eye_mark and i-eye_end_idx>=frames_gap:
                if eye_end_idx-eye_first_idx>=8*frames_gap:
                    tmp_res={
                        "periods":[self.time_list[eye_first_idx],self.time_list[eye_end_idx]],
                        "category":1
                    }
                    self.return_res.append(tmp_res)
                    self.tishi(1)
                eye_first_idx=-1
                eye_mark=False
            
            if 2 in res:
                if phone_first_idx==-1:
                    phone_first_idx=i
                    phone_end_idx=i
                    phone_mark=True
                else:
                    phone_end_idx=i
            if phone_mark and i-phone_end_idx>=frames_gap:
                if phone_end_idx-phone_first_idx>=8*frames_gap:
                    tmp_res={
                        "periods":[self.time_list[phone_first_idx],self.time_list[phone_end_idx]],
                        "category":3
                    }
                    self.return_res.append(tmp_res)
                    self.tishi(3)
                phone_first_idx=-1
                phone_mark=False

            end2end_time = time.time() - end2end_start
            print(end2end_time)
        
        self.finalRes()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    obj=edgeAndCloud()
    obj.get_init_info()
    obj.getToken()
    obj.load_model()
    obj.start()
