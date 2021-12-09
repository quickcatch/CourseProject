from clustering import get_file_names
import sys,os
from shutil import copyfile
if len(sys.argv) < 3:
    sys.exit(1)
filenames = get_file_names(sys.argv[1])
if not os.path.exists(sys.argv[2]): #output dir
    os.mkdir(sys.argv[2])
for f in filenames:
    new_path = os.path.join(sys.argv[2],f)
    without_file = "/".join(new_path.split("/")[:-1])
    os.makedirs(without_file,exist_ok=True)
    copyfile(f,new_path)

