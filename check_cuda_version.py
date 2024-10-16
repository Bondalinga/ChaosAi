import torch
import os

def get_cuda_version():
    if torch.cuda.is_available():
        version = torch.version.cuda
        if version:
            return version
    return None

def write_cuda_version():
    cuda_version = get_cuda_version()
    with open('cuda_version.txt', 'w') as f:
        if cuda_version:
            f.write(cuda_version)
        else:
            f.write('None')

if __name__ == '__main__':
    write_cuda_version()
