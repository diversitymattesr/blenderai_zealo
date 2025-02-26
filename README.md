# blenderai_zealo

<p align="left">
  English |
  <a href="./doc/README-CN.md">简体中文</a>
</p>

[![Blender Version](https://img.shields.io/badge/Blender-3.6%2B-orange)](https://www.blender.org/)
[![License](https://img.shields.io/badge/License-GPLv3-blue)](https://www.gnu.org/licenses/gpl-3.0.en.html)
[![GitHub Release](https://img.shields.io/badge/Release-latest-green)](https://github.com/diversitymattesr/blenderai_zealo/releases)
[![Modelscope](https://img.shields.io/badge/Modelscope-Repo-purple)](https://www.modelscope.cn/models/zhiliaomatters/blenderai_zealo)

A Blender addon that can use tripo API or locally running trellis generator to generate 3D models. Designed to provide blender users to make 3D models using AI easily. Note: The tripo API is a charged service while trellis generator is running in local so it is free. 

## Table of Contents
- [Features](#features)
- [Pre-requirements](#pre-requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Support](#support)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Features
- Utilize Tripo API to generate 3D models. No need to use its website. Handy for the blender users.
- Take advantages of the powerful trellis released by Microsoft Trellis team. 
- This project optimize the official trellis code so it can run in a low vram(checked peak VRAM is 4.6GB)

## Pre-requirements
- Windows 10 or later
- Blender with a relatively newer version
- Nvidia Card with cuda support and have vram > 4.6GB

## Installation
1. Download the latest release from [Releases Page](https://github.com/diversitymattesr/blenderai_zealo/releases)
2. In Blender:
   - Go to `Edit > Preferences > Add-ons`
   - Click `Install from disk` and select the downloaded `.zip` file
   - Enable the addon by checking the checkbox
   - Set the Tripo API key in preference section at bottom so that you can use Tripo service. Get [Tripo API key](https://platform.tripo3d.ai/api-keys)

## Usage
### Basic Usage
1. Access the side panel in: 3D View > Sidebar > AI Generator (Or hot key N to open side panel)
2. In newly open AI Generator panel, it shows all AI generator status eg. whether API key for tripo is correct, whether python dependencies is installed or whether trellis AI model is downloaded for making ready. Just follow the button to make ready every AI generator. 
   - For Tripo Generator
     - `Step1`: Check whether python dependencies is installed. 
     - `Step2`: Check whether API key is correct.
   - For Trellis Generator
     - `Step1`: Check whether Nvidia Driver version >= 527.41. 
     - `Step2`: Check whether python dependencies is installed. 
     - `Step3`: First time when you make ready trellis generator, it would take long time to download all needed AI models
   - How to chooseTrellis Generator startup parameters: if you have low vram, then you better choose `device: dynamic + precision: float16`. When you choose other options, the required vram is increasing.
4. When AI generators is ready. Click the buttons and open a separated panel
   - Tripo Generator: currently support text to 3d and image to 3d. Click the add button and input the text or choose an image. Other task parameters is easily understood. And then wait for the task finished and then import the result.
   -Trellis Generator: currently only support image to 3d. Click the add button and choose your image and then wait for the task to complete. And then import your result.

### Demo
[WIP]()

## Configuration
- Access settings through `Edit > Preferences > Add-ons > blenderai_zealo`
- Key configurations:
  - Input the Tripo API Key


## Support
### Known Issues
- None yet: looking forward you raising an issue 

### Troubleshooting
- None yet: looking forward adding some troubleshooting

### Reporting Issues
Please report bugs and feature requests on [GitHub Issues](https://github.com/diversitymattesr/blenderai_zealo/issues)

## Contributing
We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License
This project is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html) - compatible with Blender's licensing requirements.

## Acknowledgements
1. [Trellis](https://github.com/microsoft/TRELLIS)
