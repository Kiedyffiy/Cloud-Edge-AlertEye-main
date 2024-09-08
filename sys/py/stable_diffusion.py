import replicate


models_name = ("cjwbw/anything-v4.0",
               "cjwbw/anything-v3-better-vae",
               "cjwbw/pastel-mix",
               "nitrosocke/redshift-diffusion")
models_api = ("42a996d39a96aedc57b2e0aa8105dea39c9c89d9d266caf6bb4327a1c191b061",
              "09a5805203f4c12da649ec1923bb7729517ca25fcac790e640eaa9ed66573b65",
              "0c9ff376fe89e11daecf5a3781d782acc69415b2f1fa910460c59e5325ed86f7",
              "b78a34f0ec6d21d22ae3b10afd52b219cec65f63362e69e81e4dce07a8154ef8")


def get_stable_diffusion_img(json,api_token,models_index = 0):
    model = replicate.Client(api_token=api_token).models.get(
        models_name[models_index])
    version = model.versions.get(models_api[models_index])
    inputs = {
        # 提示词
        'prompt': json['prompt'],
        # 分辨率
        'width': json['width'],
        'height': json['height'],
        # 反向提示词
        'negative_prompt': json['negative_prompt'],
        # 输出图片数量
        # Range: 1 to 4
        'num_outputs': 1,
        # Number of denoising steps
        # Range: 1 to 500
        'num_inference_steps': json['num_inference_steps'],

        # Scale for classifier-free guidance
        # Range: 1 to 20
        'guidance_scale': json['guidance_scale'],

        # Choose a scheduler.
        'scheduler': json['scheduler'],

        # Random seed. Leave blank to randomize the seed
        'seed': json['seed'],
    }
    output = version.predict(**inputs)
    return output


if __name__ == '__main__':
    print(get_stable_diffusion_img({
        "prompt": "(golden orange gradient hair)),(red eyes),(game_cg),(double_bun),(low twintails),solo,((flat_chest)),((glasses)),(symbol in eye),masterpiece,best quality,highly detailed,1girl,(artbook),(incredibly_absurdres),huge_filesize,((yellow necktie)),(trench coat),((pleated_skirt)),small breasts,Exquisite background,sit on the sofa,laugh,((library)",
        "width": 768,
        "height": 512,
        "negative_prompt": "",
        "num_inference_steps": 50,
        "guidance_scale": 10,
        "scheduler": "K_EULER_ANCESTRAL",
        "seed": 1
    },""))
