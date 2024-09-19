import base64
import os
import argparse
from openai import OpenAI


def main():
    parser = argparse.ArgumentParser(description="Generate images from text prompts")
    parser.add_argument("--prompt", type=str, required=True, help="User prompt")
    parser.add_argument("--model", type=str, help="Model name")
    parser.add_argument("--file_name", type=str, default="output.jpg", help="Name of the output file")
    parser.add_argument("--quality", type=str, choices=['standard', 'hd', 'quick', 'manual'], default='standard',
                        help="Image quality")
    parser.add_argument("--size", type=str, default="1024x1024", help="Image size (height x width)")
    parser.add_argument("--style", type=str, choices=['vivid', 'natural', 'artistic'], default='vivid',
                        help="Image style")
    parser.add_argument("--guidance_scale", type=float, help="Guidance scale for image generation")
    parser.add_argument("--num_inference_steps", type=int, help="Number of inference steps")
    args = parser.parse_args()

    imagegen_url = os.getenv("IMAGEGEN_OPENAI_BASE_URL")
    assert imagegen_url is not None, "IMAGEGEN_OPENAI_BASE_URL environment variable is not set"
    server_api_key = os.getenv('IMAGEGEN_OPENAI_API_KEY', 'EMPTY')

    if not args.model:
        imagegen_model = os.getenv('IMAGEGEN_OPENAI_MODEL')
        assert imagegen_model is not None, "IMAGEGEN_OPENAI_MODEL environment variable is not set"
        args.model = imagegen_model

    client = OpenAI(base_url=imagegen_url, api_key=server_api_key)

    if imagegen_url == "https://api.gpt.h2o.ai/v1":
        available_models = ['playv2', 'flux.1-schnell']
        if args.model not in available_models:
            print(f"Warning: Model {args.model} not in available models {available_models}. Using default.")
            args.model = available_models[0]
    elif imagegen_url == "https://api.openai.com/v1":
        # https://platform.openai.com/docs/api-reference/images/create
        available_models = ['dall-e-2', 'dall-e-3']
        if args.model not in available_models:
            print(f"Warning: Model {args.model} not in available models {available_models}. Using default.")
            args.model = 'dall-e-2'

        max_chars = 1000 if args.model == 'dall-e-2' else 4000
        args.prompt = args.prompt[:max_chars]

        if args.model == 'dall-e-2':
            valid_sizes = ['256x256', '512x512', '1024x1024']
        else:
            valid_sizes = ['1024x1024', '1792x1024', '1024x1792']

        if args.size not in valid_sizes:
            print(f"Warning: Size {args.size} not valid for {args.model}. Using default.")
            args.size = valid_sizes[0]

        args.quality = 'standard' if args.quality not in ['standard', 'hd'] else args.quality
        args.style = 'vivid' if args.style not in ['vivid', 'natural'] else args.style

    generation_params = {
        "prompt": args.prompt,
        "model": args.model,
        "quality": args.quality,
        "size": args.size,
        "style": args.style,
    }

    if imagegen_url != "https://api.openai.com/v1":
        extra_body = {}
        if args.guidance_scale:
            extra_body["guidance_scale"] = args.guidance_scale
        if args.num_inference_steps:
            extra_body["num_inference_steps"] = args.num_inference_steps
        if extra_body:
            generation_params["extra_body"] = extra_body

    response = client.images.generate(**generation_params)

    image_data_base64 = response.data[0].b64_json
    image_data = base64.b64decode(image_data_base64)

    # Save the image to a file
    base_path = os.getenv("H2OGPT_OPENAI_BASE_FILE_PATH", "./openai_files/")
    # Create the directory if it doesn't exist
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    full_path = os.path.join(base_path, args.file_name)

    # Write the image data to a file
    with open(full_path, "wb") as img_file:
        img_file.write(image_data)

    print(f"Image successfully saved to the path: {full_path}")


if __name__ == "__main__":
    main()
