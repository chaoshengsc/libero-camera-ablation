window.RESULTS = [
 {
  "id": "act_cube_500",
  "model": "ACT",
  "task": "ALOHA Transfer Cube",
  "sim": "MuJoCo",
  "checkpoint": "lerobot/act_aloha_sim_transfer_cube_human@ba73b276",
  "baseline_pc": 83.0,
  "baseline_n": 500,
  "baseline_src": "HF 仓库自带 eval_info.json(500 回合)",
  "status": "done",
  "pc": 83.2,
  "n": 500,
  "tasks": [
   {
    "id": 0,
    "name": "ALOHA Transfer Cube",
    "ok": 416,
    "n": 500
   }
  ],
  "videos": [
   {
    "src": "data/act_cube_500/videos/aloha_0/eval_episode_0.mp4",
    "ep": 0,
    "success": false,
    "reward": 80.0,
    "task": "ALOHA Transfer Cube"
   },
   {
    "src": "data/act_cube_500/videos/aloha_0/eval_episode_1.mp4",
    "ep": 1,
    "success": true,
    "reward": 158.0,
    "task": "ALOHA Transfer Cube"
   },
   {
    "src": "data/act_cube_500/videos/aloha_0/eval_episode_2.mp4",
    "ep": 2,
    "success": true,
    "reward": 202.0,
    "task": "ALOHA Transfer Cube"
   },
   {
    "src": "data/act_cube_500/videos/aloha_0/eval_episode_3.mp4",
    "ep": 3,
    "success": true,
    "reward": 288.0,
    "task": "ALOHA Transfer Cube"
   },
   {
    "src": "data/act_cube_500/videos/aloha_0/eval_episode_4.mp4",
    "ep": 4,
    "success": true,
    "reward": 282.0,
    "task": "ALOHA Transfer Cube"
   },
   {
    "src": "data/act_cube_500/videos/aloha_0/eval_episode_5.mp4",
    "ep": 5,
    "success": false,
    "reward": 60.0,
    "task": "ALOHA Transfer Cube"
   },
   {
    "src": "data/act_cube_500/videos/aloha_0/eval_episode_6.mp4",
    "ep": 6,
    "success": true,
    "reward": 266.0,
    "task": "ALOHA Transfer Cube"
   },
   {
    "src": "data/act_cube_500/videos/aloha_0/eval_episode_7.mp4",
    "ep": 7,
    "success": true,
    "reward": 258.0,
    "task": "ALOHA Transfer Cube"
   },
   {
    "src": "data/act_cube_500/videos/aloha_0/eval_episode_8.mp4",
    "ep": 8,
    "success": true,
    "reward": 254.0,
    "task": "ALOHA Transfer Cube"
   },
   {
    "src": "data/act_cube_500/videos/aloha_0/eval_episode_9.mp4",
    "ep": 9,
    "success": false,
    "reward": 75.0,
    "task": "ALOHA Transfer Cube"
   }
  ],
  "ci": 3.3,
  "baseline_ci": 3.3
 },
 {
  "id": "openvla_spatial_500",
  "model": "OpenVLA",
  "task": "LIBERO-Spatial",
  "sim": "MuJoCo",
  "checkpoint": "openvla/openvla-7b-finetuned-libero-spatial@962318ce",
  "baseline_pc": 84.7,
  "baseline_pm": 0.9,
  "baseline_src": "openvla README(3 种子 × 500 回合,A100)",
  "status": "done",
  "pc": 86.2,
  "n": 500,
  "tasks": [
   {
    "id": 0,
    "name": "盘子与小烤碗之间",
    "ok": 43,
    "n": 50
   },
   {
    "id": 1,
    "name": "小烤碗旁",
    "ok": 47,
    "n": 50
   },
   {
    "id": 2,
    "name": "桌子中央",
    "ok": 46,
    "n": 50
   },
   {
    "id": 3,
    "name": "饼干盒上",
    "ok": 49,
    "n": 50
   },
   {
    "id": 4,
    "name": "木柜上层抽屉里",
    "ok": 38,
    "n": 50
   },
   {
    "id": 5,
    "name": "小烤碗上",
    "ok": 46,
    "n": 50
   },
   {
    "id": 6,
    "name": "饼干盒旁",
    "ok": 45,
    "n": 50
   },
   {
    "id": 7,
    "name": "灶台上",
    "ok": 41,
    "n": 50
   },
   {
    "id": 8,
    "name": "盘子旁",
    "ok": 40,
    "n": 50
   },
   {
    "id": 9,
    "name": "木柜顶上",
    "ok": 36,
    "n": 50
   }
  ],
  "videos": [
   {
    "src": "data/openvla_spatial_500/videos/task0_ok.mp4",
    "ep": 0,
    "success": true,
    "task": "盘子与小烤碗之间",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task0_fail.mp4",
    "ep": 1,
    "success": false,
    "task": "盘子与小烤碗之间",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task1_ok.mp4",
    "ep": 0,
    "success": true,
    "task": "小烤碗旁",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task1_fail.mp4",
    "ep": 33,
    "success": false,
    "task": "小烤碗旁",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task2_ok.mp4",
    "ep": 0,
    "success": true,
    "task": "桌子中央",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task2_fail.mp4",
    "ep": 4,
    "success": false,
    "task": "桌子中央",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task3_ok.mp4",
    "ep": 0,
    "success": true,
    "task": "饼干盒上",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task3_fail.mp4",
    "ep": 2,
    "success": false,
    "task": "饼干盒上",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task4_ok.mp4",
    "ep": 0,
    "success": true,
    "task": "木柜上层抽屉里",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task4_fail.mp4",
    "ep": 1,
    "success": false,
    "task": "木柜上层抽屉里",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task5_ok.mp4",
    "ep": 0,
    "success": true,
    "task": "小烤碗上",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task5_fail.mp4",
    "ep": 10,
    "success": false,
    "task": "小烤碗上",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task6_ok.mp4",
    "ep": 0,
    "success": true,
    "task": "饼干盒旁",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task6_fail.mp4",
    "ep": 8,
    "success": false,
    "task": "饼干盒旁",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task7_ok.mp4",
    "ep": 0,
    "success": true,
    "task": "灶台上",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task7_fail.mp4",
    "ep": 7,
    "success": false,
    "task": "灶台上",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task8_ok.mp4",
    "ep": 0,
    "success": true,
    "task": "盘子旁",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task8_fail.mp4",
    "ep": 2,
    "success": false,
    "task": "盘子旁",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task9_ok.mp4",
    "ep": 0,
    "success": true,
    "task": "木柜顶上",
    "reward": null
   },
   {
    "src": "data/openvla_spatial_500/videos/task9_fail.mp4",
    "ep": 1,
    "success": false,
    "task": "木柜顶上",
    "reward": null
   }
  ],
  "ci": 3.0
 },
 {
  "id": "smolvla_hfvla_500",
  "model": "SmolVLA",
  "task": "LIBERO-Spatial",
  "sim": "MuJoCo",
  "checkpoint": "HuggingFaceVLA/smolvla_libero@6721902b",
  "baseline_pc": 90.0,
  "baseline_n": 100,
  "baseline_src": "SmolVLA 论文 Table 2(每任务 10 次);公开权重与论文结构不同,社区同权重实测约 82%",
  "status": "done",
  "pc": 75.2,
  "n": 500,
  "tasks": [
   {
    "id": 0,
    "name": "盘子与小烤碗之间",
    "ok": 30,
    "n": 50
   },
   {
    "id": 1,
    "name": "小烤碗旁",
    "ok": 45,
    "n": 50
   },
   {
    "id": 2,
    "name": "桌子中央",
    "ok": 45,
    "n": 50
   },
   {
    "id": 3,
    "name": "饼干盒上",
    "ok": 38,
    "n": 50
   },
   {
    "id": 4,
    "name": "木柜上层抽屉里",
    "ok": 31,
    "n": 50
   },
   {
    "id": 5,
    "name": "小烤碗上",
    "ok": 43,
    "n": 50
   },
   {
    "id": 6,
    "name": "饼干盒旁",
    "ok": 36,
    "n": 50
   },
   {
    "id": 7,
    "name": "灶台上",
    "ok": 34,
    "n": 50
   },
   {
    "id": 8,
    "name": "盘子旁",
    "ok": 42,
    "n": 50
   },
   {
    "id": 9,
    "name": "木柜顶上",
    "ok": 32,
    "n": 50
   }
  ],
  "videos": [
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_0/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "盘子与小烤碗之间"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_0/eval_episode_1.mp4",
    "ep": 1,
    "success": false,
    "reward": null,
    "task": "盘子与小烤碗之间"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_1/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "小烤碗旁"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_1/eval_episode_4.mp4",
    "ep": 4,
    "success": false,
    "reward": null,
    "task": "小烤碗旁"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_2/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "桌子中央"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_2/eval_episode_8.mp4",
    "ep": 8,
    "success": false,
    "reward": null,
    "task": "桌子中央"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_3/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "饼干盒上"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_3/eval_episode_3.mp4",
    "ep": 3,
    "success": false,
    "reward": null,
    "task": "饼干盒上"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_4/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "木柜上层抽屉里"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_4/eval_episode_1.mp4",
    "ep": 1,
    "success": false,
    "reward": null,
    "task": "木柜上层抽屉里"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_5/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "小烤碗上"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_5/eval_episode_1.mp4",
    "ep": 1,
    "success": false,
    "reward": null,
    "task": "小烤碗上"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_6/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "饼干盒旁"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_6/eval_episode_1.mp4",
    "ep": 1,
    "success": false,
    "reward": null,
    "task": "饼干盒旁"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_7/eval_episode_1.mp4",
    "ep": 1,
    "success": true,
    "reward": null,
    "task": "灶台上"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_7/eval_episode_0.mp4",
    "ep": 0,
    "success": false,
    "reward": null,
    "task": "灶台上"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_8/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "盘子旁"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_8/eval_episode_4.mp4",
    "ep": 4,
    "success": false,
    "reward": null,
    "task": "盘子旁"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_9/eval_episode_2.mp4",
    "ep": 2,
    "success": true,
    "reward": null,
    "task": "木柜顶上"
   },
   {
    "src": "data/smolvla_hfvla_500/videos/libero_spatial_9/eval_episode_0.mp4",
    "ep": 0,
    "success": false,
    "reward": null,
    "task": "木柜顶上"
   }
  ],
  "ci": 3.8,
  "baseline_ci": 5.9
 },
 {
  "id": "pi05_spatial_500",
  "model": "π0.5",
  "task": "LIBERO-Spatial",
  "sim": "MuJoCo",
  "checkpoint": "lerobot/pi05_libero_finetuned_v044@8e174154",
  "baseline_pc": 98.8,
  "baseline_src": "OpenPI LIBERO README(LeRobot 文档复现为 97.0%)",
  "status": "done",
  "pc": 98.0,
  "n": 500,
  "tasks": [
   {
    "id": 0,
    "name": "盘子与小烤碗之间",
    "ok": 50,
    "n": 50
   },
   {
    "id": 1,
    "name": "小烤碗旁",
    "ok": 50,
    "n": 50
   },
   {
    "id": 2,
    "name": "桌子中央",
    "ok": 49,
    "n": 50
   },
   {
    "id": 3,
    "name": "饼干盒上",
    "ok": 50,
    "n": 50
   },
   {
    "id": 4,
    "name": "木柜上层抽屉里",
    "ok": 46,
    "n": 50
   },
   {
    "id": 5,
    "name": "小烤碗上",
    "ok": 46,
    "n": 50
   },
   {
    "id": 6,
    "name": "饼干盒旁",
    "ok": 50,
    "n": 50
   },
   {
    "id": 7,
    "name": "灶台上",
    "ok": 49,
    "n": 50
   },
   {
    "id": 8,
    "name": "盘子旁",
    "ok": 50,
    "n": 50
   },
   {
    "id": 9,
    "name": "木柜顶上",
    "ok": 50,
    "n": 50
   }
  ],
  "videos": [
   {
    "src": "data/pi05_spatial_500/videos/libero_spatial_0/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "盘子与小烤碗之间"
   },
   {
    "src": "data/pi05_spatial_500/videos/libero_spatial_1/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "小烤碗旁"
   },
   {
    "src": "data/pi05_spatial_500/videos/libero_spatial_2/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "桌子中央"
   },
   {
    "src": "data/pi05_spatial_500/videos/libero_spatial_3/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "饼干盒上"
   },
   {
    "src": "data/pi05_spatial_500/videos/libero_spatial_4/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "木柜上层抽屉里"
   },
   {
    "src": "data/pi05_spatial_500/videos/libero_spatial_5/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "小烤碗上"
   },
   {
    "src": "data/pi05_spatial_500/videos/libero_spatial_6/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "饼干盒旁"
   },
   {
    "src": "data/pi05_spatial_500/videos/libero_spatial_7/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "灶台上"
   },
   {
    "src": "data/pi05_spatial_500/videos/libero_spatial_7/eval_episode_1.mp4",
    "ep": 1,
    "success": false,
    "reward": null,
    "task": "灶台上"
   },
   {
    "src": "data/pi05_spatial_500/videos/libero_spatial_8/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "盘子旁"
   },
   {
    "src": "data/pi05_spatial_500/videos/libero_spatial_9/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "木柜顶上"
   }
  ],
  "ci": 1.2
 },
 {
  "id": "pi0_spatial_500",
  "model": "π0",
  "task": "LIBERO-Spatial",
  "sim": "MuJoCo",
  "checkpoint": "lerobot/pi0_libero_finetuned_v044@45dcc8fc",
  "baseline_pc": 96.8,
  "baseline_src": "OpenPI LIBERO README 旧版(commit c015073f,π0 @30k)",
  "status": "done",
  "pc": 73.4,
  "n": 500,
  "tasks": [
   {
    "id": 0,
    "name": "盘子与小烤碗之间",
    "ok": 34,
    "n": 50
   },
   {
    "id": 1,
    "name": "小烤碗旁",
    "ok": 43,
    "n": 50
   },
   {
    "id": 2,
    "name": "桌子中央",
    "ok": 46,
    "n": 50
   },
   {
    "id": 3,
    "name": "饼干盒上",
    "ok": 42,
    "n": 50
   },
   {
    "id": 4,
    "name": "木柜上层抽屉里",
    "ok": 29,
    "n": 50
   },
   {
    "id": 5,
    "name": "小烤碗上",
    "ok": 32,
    "n": 50
   },
   {
    "id": 6,
    "name": "饼干盒旁",
    "ok": 39,
    "n": 50
   },
   {
    "id": 7,
    "name": "灶台上",
    "ok": 40,
    "n": 50
   },
   {
    "id": 8,
    "name": "盘子旁",
    "ok": 34,
    "n": 50
   },
   {
    "id": 9,
    "name": "木柜顶上",
    "ok": 28,
    "n": 50
   }
  ],
  "videos": [
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_0/eval_episode_1.mp4",
    "ep": 1,
    "success": true,
    "reward": null,
    "task": "盘子与小烤碗之间"
   },
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_0/eval_episode_0.mp4",
    "ep": 0,
    "success": false,
    "reward": null,
    "task": "盘子与小烤碗之间"
   },
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_1/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "小烤碗旁"
   },
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_2/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "桌子中央"
   },
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_2/eval_episode_1.mp4",
    "ep": 1,
    "success": false,
    "reward": null,
    "task": "桌子中央"
   },
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_3/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "饼干盒上"
   },
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_3/eval_episode_7.mp4",
    "ep": 7,
    "success": false,
    "reward": null,
    "task": "饼干盒上"
   },
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_4/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "木柜上层抽屉里"
   },
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_4/eval_episode_1.mp4",
    "ep": 1,
    "success": false,
    "reward": null,
    "task": "木柜上层抽屉里"
   },
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_5/eval_episode_1.mp4",
    "ep": 1,
    "success": true,
    "reward": null,
    "task": "小烤碗上"
   },
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_5/eval_episode_0.mp4",
    "ep": 0,
    "success": false,
    "reward": null,
    "task": "小烤碗上"
   },
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_6/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "饼干盒旁"
   },
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_6/eval_episode_2.mp4",
    "ep": 2,
    "success": false,
    "reward": null,
    "task": "饼干盒旁"
   },
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_7/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "灶台上"
   },
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_7/eval_episode_5.mp4",
    "ep": 5,
    "success": false,
    "reward": null,
    "task": "灶台上"
   },
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_8/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "盘子旁"
   },
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_8/eval_episode_1.mp4",
    "ep": 1,
    "success": false,
    "reward": null,
    "task": "盘子旁"
   },
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_9/eval_episode_0.mp4",
    "ep": 0,
    "success": true,
    "reward": null,
    "task": "木柜顶上"
   },
   {
    "src": "data/pi0_spatial_500/videos/libero_spatial_9/eval_episode_1.mp4",
    "ep": 1,
    "success": false,
    "reward": null,
    "task": "木柜顶上"
   }
  ],
  "ci": 3.9
 },
 {
  "id": "dp_pusht_500",
  "model": "Diffusion Policy",
  "task": "PushT",
  "sim": "2D(pymunk)",
  "checkpoint": "lerobot/diffusion_pusht@84a7c231",
  "baseline_pc": 65.4,
  "baseline_n": 500,
  "baseline_src": "LeRobot 模型卡(500 回合;原版 DP 仓库同等模型 64.2%)",
  "status": "done",
  "pc": 63.0,
  "n": 500,
  "tasks": [
   {
    "id": 0,
    "name": "PushT",
    "ok": 315,
    "n": 500
   }
  ],
  "videos": [
   {
    "src": "data/dp_pusht_500/videos/pusht_0/eval_episode_0.mp4",
    "ep": 0,
    "success": false,
    "reward": 167.0,
    "task": "PushT"
   },
   {
    "src": "data/dp_pusht_500/videos/pusht_0/eval_episode_1.mp4",
    "ep": 1,
    "success": false,
    "reward": 78.8,
    "task": "PushT"
   },
   {
    "src": "data/dp_pusht_500/videos/pusht_0/eval_episode_2.mp4",
    "ep": 2,
    "success": true,
    "reward": 222.2,
    "task": "PushT"
   },
   {
    "src": "data/dp_pusht_500/videos/pusht_0/eval_episode_3.mp4",
    "ep": 3,
    "success": false,
    "reward": 248.8,
    "task": "PushT"
   },
   {
    "src": "data/dp_pusht_500/videos/pusht_0/eval_episode_4.mp4",
    "ep": 4,
    "success": true,
    "reward": 147.7,
    "task": "PushT"
   },
   {
    "src": "data/dp_pusht_500/videos/pusht_0/eval_episode_5.mp4",
    "ep": 5,
    "success": false,
    "reward": 84.3,
    "task": "PushT"
   },
   {
    "src": "data/dp_pusht_500/videos/pusht_0/eval_episode_6.mp4",
    "ep": 6,
    "success": true,
    "reward": 82.0,
    "task": "PushT"
   },
   {
    "src": "data/dp_pusht_500/videos/pusht_0/eval_episode_7.mp4",
    "ep": 7,
    "success": true,
    "reward": 142.3,
    "task": "PushT"
   },
   {
    "src": "data/dp_pusht_500/videos/pusht_0/eval_episode_8.mp4",
    "ep": 8,
    "success": false,
    "reward": 95.6,
    "task": "PushT"
   },
   {
    "src": "data/dp_pusht_500/videos/pusht_0/eval_episode_9.mp4",
    "ep": 9,
    "success": false,
    "reward": 196.8,
    "task": "PushT"
   }
  ],
  "ci": 4.2,
  "baseline_ci": 4.2
 }
];
window.LIBERO_TASKS = ["盘子与小烤碗之间", "小烤碗旁", "桌子中央", "饼干盒上", "木柜上层抽屉里", "小烤碗上", "饼干盒旁", "灶台上", "盘子旁", "木柜顶上"];
window.BLACKOUT = {"summary": [{"model": "OpenVLA", "normal": [8, 10, 9, 9, 8, 10, 9, 8, 5, 5], "black": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}, {"model": "SmolVLA", "normal": [6, 8, 9, 7, 7, 7, 8, 7, 9, 4], "black": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}, {"model": "pi0", "normal": [7, 10, 7, 9, 7, 8, 7, 9, 6, 6], "black": [7, 8, 9, 8, 6, 1, 9, 0, 7, 1]}, {"model": "pi0.5", "normal": [10, 10, 10, 10, 10, 10, 10, 9, 10, 10], "black": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}], "runs": [{"id": "pi0_black_all", "model": "π0", "task": "LIBERO-Spatial", "status": "done", "pc": 56.0, "n": 100, "tasks": [{"id": 0, "name": "盘子与小烤碗之间", "ok": 7, "n": 10}, {"id": 1, "name": "小烤碗旁", "ok": 8, "n": 10}, {"id": 2, "name": "桌子中央", "ok": 9, "n": 10}, {"id": 3, "name": "饼干盒上", "ok": 8, "n": 10}, {"id": 4, "name": "木柜上层抽屉里", "ok": 6, "n": 10}, {"id": 5, "name": "小烤碗上", "ok": 1, "n": 10}, {"id": 6, "name": "饼干盒旁", "ok": 9, "n": 10}, {"id": 7, "name": "灶台上", "ok": 0, "n": 10}, {"id": 8, "name": "盘子旁", "ok": 7, "n": 10}, {"id": 9, "name": "木柜顶上", "ok": 1, "n": 10}], "videos": [{"src": "data/pi0_black_all/videos/libero_spatial_0/eval_episode_1.mp4", "ep": 1, "success": true, "reward": null, "task": "盘子与小烤碗之间"}, {"src": "data/pi0_black_all/videos/libero_spatial_0/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "盘子与小烤碗之间"}, {"src": "data/pi0_black_all/videos/libero_spatial_1/eval_episode_1.mp4", "ep": 1, "success": true, "reward": null, "task": "小烤碗旁"}, {"src": "data/pi0_black_all/videos/libero_spatial_1/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "小烤碗旁"}, {"src": "data/pi0_black_all/videos/libero_spatial_2/eval_episode_1.mp4", "ep": 1, "success": true, "reward": null, "task": "桌子中央"}, {"src": "data/pi0_black_all/videos/libero_spatial_2/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "桌子中央"}, {"src": "data/pi0_black_all/videos/libero_spatial_3/eval_episode_0.mp4", "ep": 0, "success": true, "reward": null, "task": "饼干盒上"}, {"src": "data/pi0_black_all/videos/libero_spatial_3/eval_episode_2.mp4", "ep": 2, "success": false, "reward": null, "task": "饼干盒上"}, {"src": "data/pi0_black_all/videos/libero_spatial_4/eval_episode_0.mp4", "ep": 0, "success": true, "reward": null, "task": "木柜上层抽屉里"}, {"src": "data/pi0_black_all/videos/libero_spatial_4/eval_episode_1.mp4", "ep": 1, "success": false, "reward": null, "task": "木柜上层抽屉里"}, {"src": "data/pi0_black_all/videos/libero_spatial_5/eval_episode_9.mp4", "ep": 9, "success": true, "reward": null, "task": "小烤碗上"}, {"src": "data/pi0_black_all/videos/libero_spatial_5/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "小烤碗上"}, {"src": "data/pi0_black_all/videos/libero_spatial_6/eval_episode_0.mp4", "ep": 0, "success": true, "reward": null, "task": "饼干盒旁"}, {"src": "data/pi0_black_all/videos/libero_spatial_6/eval_episode_1.mp4", "ep": 1, "success": false, "reward": null, "task": "饼干盒旁"}, {"src": "data/pi0_black_all/videos/libero_spatial_7/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "灶台上"}, {"src": "data/pi0_black_all/videos/libero_spatial_8/eval_episode_0.mp4", "ep": 0, "success": true, "reward": null, "task": "盘子旁"}, {"src": "data/pi0_black_all/videos/libero_spatial_8/eval_episode_2.mp4", "ep": 2, "success": false, "reward": null, "task": "盘子旁"}, {"src": "data/pi0_black_all/videos/libero_spatial_9/eval_episode_4.mp4", "ep": 4, "success": true, "reward": null, "task": "木柜顶上"}, {"src": "data/pi0_black_all/videos/libero_spatial_9/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "木柜顶上"}]}, {"id": "pi05_black_all", "model": "π0.5", "task": "LIBERO-Spatial", "status": "done", "pc": 0.0, "n": 100, "tasks": [{"id": 0, "name": "盘子与小烤碗之间", "ok": 0, "n": 10}, {"id": 1, "name": "小烤碗旁", "ok": 0, "n": 10}, {"id": 2, "name": "桌子中央", "ok": 0, "n": 10}, {"id": 3, "name": "饼干盒上", "ok": 0, "n": 10}, {"id": 4, "name": "木柜上层抽屉里", "ok": 0, "n": 10}, {"id": 5, "name": "小烤碗上", "ok": 0, "n": 10}, {"id": 6, "name": "饼干盒旁", "ok": 0, "n": 10}, {"id": 7, "name": "灶台上", "ok": 0, "n": 10}, {"id": 8, "name": "盘子旁", "ok": 0, "n": 10}, {"id": 9, "name": "木柜顶上", "ok": 0, "n": 10}], "videos": [{"src": "data/pi05_black_all/videos/libero_spatial_0/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "盘子与小烤碗之间"}, {"src": "data/pi05_black_all/videos/libero_spatial_1/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "小烤碗旁"}, {"src": "data/pi05_black_all/videos/libero_spatial_2/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "桌子中央"}, {"src": "data/pi05_black_all/videos/libero_spatial_3/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "饼干盒上"}, {"src": "data/pi05_black_all/videos/libero_spatial_4/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "木柜上层抽屉里"}, {"src": "data/pi05_black_all/videos/libero_spatial_5/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "小烤碗上"}, {"src": "data/pi05_black_all/videos/libero_spatial_6/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "饼干盒旁"}, {"src": "data/pi05_black_all/videos/libero_spatial_7/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "灶台上"}, {"src": "data/pi05_black_all/videos/libero_spatial_8/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "盘子旁"}, {"src": "data/pi05_black_all/videos/libero_spatial_9/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "木柜顶上"}]}, {"id": "smolvla_black_all", "model": "SmolVLA", "task": "LIBERO-Spatial", "status": "done", "pc": 0.0, "n": 100, "tasks": [{"id": 0, "name": "盘子与小烤碗之间", "ok": 0, "n": 10}, {"id": 1, "name": "小烤碗旁", "ok": 0, "n": 10}, {"id": 2, "name": "桌子中央", "ok": 0, "n": 10}, {"id": 3, "name": "饼干盒上", "ok": 0, "n": 10}, {"id": 4, "name": "木柜上层抽屉里", "ok": 0, "n": 10}, {"id": 5, "name": "小烤碗上", "ok": 0, "n": 10}, {"id": 6, "name": "饼干盒旁", "ok": 0, "n": 10}, {"id": 7, "name": "灶台上", "ok": 0, "n": 10}, {"id": 8, "name": "盘子旁", "ok": 0, "n": 10}, {"id": 9, "name": "木柜顶上", "ok": 0, "n": 10}], "videos": [{"src": "data/smolvla_black_all/videos/libero_spatial_0/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "盘子与小烤碗之间"}, {"src": "data/smolvla_black_all/videos/libero_spatial_1/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "小烤碗旁"}, {"src": "data/smolvla_black_all/videos/libero_spatial_2/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "桌子中央"}, {"src": "data/smolvla_black_all/videos/libero_spatial_3/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "饼干盒上"}, {"src": "data/smolvla_black_all/videos/libero_spatial_4/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "木柜上层抽屉里"}, {"src": "data/smolvla_black_all/videos/libero_spatial_5/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "小烤碗上"}, {"src": "data/smolvla_black_all/videos/libero_spatial_6/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "饼干盒旁"}, {"src": "data/smolvla_black_all/videos/libero_spatial_7/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "灶台上"}, {"src": "data/smolvla_black_all/videos/libero_spatial_8/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "盘子旁"}, {"src": "data/smolvla_black_all/videos/libero_spatial_9/eval_episode_0.mp4", "ep": 0, "success": false, "reward": null, "task": "木柜顶上"}]}]};
window.FOLLOWUP = {"perturb": [{"model": "pi0", "normal": 76, "noise": 79, "freeze": 71, "all_black": 56}, {"model": "pi0.5", "normal": 99, "noise": 99, "freeze": 0, "all_black": 0}, {"model": "SmolVLA", "normal": 72, "noise": 32, "freeze": null, "all_black": 0}], "traj": {"pairs": {"噪声底线 π0正常 vs π0正常(重跑)": {"dtw_mean": 2.122763625449642, "grasp_dist_mean": 1.505813142805105, "n_grasp_pairs": 100, "dtw_by_task": [0.29611188652706033, 0.18479214756542073, 0.051296405239698195, 0.03929469684193469, 2.055231649911648, 6.599279266643554, 3.0980904528411726, 2.563128786161911, 3.0332950675391683, 3.3071158952248574]}, "π0 全涂黑 vs π0 正常": {"dtw_mean": 4.4357033580099605, "grasp_dist_mean": 5.0274308338498965, "n_grasp_pairs": 99, "dtw_by_task": [2.5641096246494266, 2.6814235774131294, 2.746972165290431, 2.4683657819989855, 2.2687679673456236, 6.023226246419891, 3.1167471225040986, 10.91678897488282, 3.7683282735958175, 7.802303845999388]}, "不同模型 π0.5 vs π0(都正常)": {"dtw_mean": 3.2752698276236725, "grasp_dist_mean": 2.6516216592657202, "n_grasp_pairs": 100, "dtw_by_task": [3.6615378842166364, 2.417387642284104, 2.613055514182866, 2.142765067554801, 2.851562554294795, 6.349897413367608, 3.112796788770379, 2.5065714384676614, 3.7633832420722024, 3.3337407310256744]}}, "grasp_spread": {"traj_pi0_normal": [2.1357074249242927, 1.3981939399718486, 1.6914565639060672, 1.4785298951118953, 1.6992973159430846, 1.6569152658310435, 1.3998327220960847, 1.853011279874711, 2.484865625142493, 2.0383281751743736], "traj_pi0_normal2": [2.1223149720481573, 1.3543052435284286, 1.6918604446210526, 1.4807442761592549, 1.8323130806994583, 1.784398375490603, 1.4669437253250028, 1.2229830313318049, 2.665826408278668, 2.2690479329397517], "traj_pi0_black": [2.224329758162991, 1.8205585687569594, 2.097622104987571, 1.855944782001093, 1.492268341188421, 1.8234230470976243, 1.5581007229857433, 6.718215283339683, 3.106580608592714, 1.3804339407217467], "traj_pi05_normal": [2.0635068565996693, 0.9843834591063043, 1.8146523832724295, 1.4699323532612216, 1.2068952296704514, 1.5262104052406502, 1.5821296555025013, 1.00959682394403, 1.7907960855230964, 2.174718134933361]}}, "cam": [{"model": "pi0", "normal": 76, "agent_black": 78, "wrist_black": 59, "all_black": 56}, {"model": "pi0.5", "normal": 99, "agent_black": 51, "wrist_black": 0, "all_black": 0}, {"model": "SmolVLA", "normal": 72, "agent_black": 2, "wrist_black": 5, "all_black": 0}], "finetune": [{"name": "原始 π0", "normal": 76, "black": 56, "note": "实验 B 同协议"}, {"name": "继续微调 · 对照(p=0)", "normal": 78.0, "black": 61.0, "note": "3000 步,batch 16,只训动作专家"}, {"name": "继续微调 · 状态置零(p=0.5)", "normal": 68.0, "black": 40.0, "note": "同上,训练时按样本 50% 置零 observation.state"}]};
