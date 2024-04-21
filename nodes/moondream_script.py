from .moondream import VisionEncoder, TextModel
from huggingface_hub import snapshot_download
import torch
import os
import hashlib
from torchvision import transforms
from pathlib import Path
import folder_paths

if torch.cuda.is_available():
    DEVICE = "cuda"
    DTYPE = torch.float16
else:
    DEVICE = "cpu"
    DTYPE = torch.float32


files_for_moondream = Path(folder_paths.folder_names_and_paths["LLavacheckpoints"][0][0]) / "files_for__moondream"
files_for_moondream.mkdir(parents=True, exist_ok=True)
output_directory = os.path.join(files_for_moondream , "output")
# Define your local directory where you want to save the files

image_encoder_cache_path = os.path.join(output_directory, "image_encoder_cache")
class MoonDream:
    def __init__(self):
        self.model_path = snapshot_download("vikhyatk/moondream1", 
                                            revision="5b39a3ffad760c4e0ae67856dcd5edf1afcd63f4", 
                                            local_dir=files_for_moondream,
                                            force_download=False,  # Set to True if you always want to download, regardless of local copy
                                            local_files_only=True,  # Set to False to allow downloading if not available locally
                                            local_dir_use_symlinks=False  # or set to True/False based on your symlink preference
                                        )
        self.vision_encoder = VisionEncoder(self.model_path)
        self.text_model = TextModel(self.model_path)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "question": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING",)

    FUNCTION = "answer_questions"

    CATEGORY = "VLM Nodes/MoonDream"

    def process_image(self, image):
        # Calculate checksum of the image

        image_array = image.numpy()  # Convert Tensor to NumPy array
        image_hash = hashlib.sha256(image_array.tobytes()).hexdigest()
        image = transforms.ToPILImage()(image[0].permute(2, 0, 1))
        # Check if `image_encoder_cache/{image_hash}.pt` exists, if so load and return it.
        # Otherwise, save the encoded image to `image_encoder_cache/{image_hash}.pt` and return it.
        cache_path = f"{image_encoder_cache_path}/{image_hash}.pt"
        if os.path.exists(cache_path):
            return torch.load(cache_path).to(DEVICE, dtype=DTYPE)
        else:
            image_vec = self.vision_encoder(image)
            os.makedirs(image_encoder_cache_path, exist_ok=True)
            torch.save(image_vec, cache_path)
            return image_vec.to(DEVICE, dtype=DTYPE)

    def answer_questions(self, image, question):
        image_embeds = self.process_image(image)
        full_sentence = self.text_model.answer_question(image_embeds, question)
        return (full_sentence,)


# A dictionary that contains all nodes you want to export with their names
NODE_CLASS_MAPPINGS = {"MoonDream": MoonDream}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {"MoonDream": "MoonDream Node"}


