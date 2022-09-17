import os
import shutil

# Build DSCSTools
os.chdir("sdmmlib")
os.chdir("dscstools")
os.system("python setup.py build_ext --inplace")
os.chdir(os.path.pardir)
os.chdir(os.path.pardir)

# Build Squirrel
os.chdir("sdmmlib")
os.chdir("squirrel")
os.system("python setup.py build_ext --inplace")
os.chdir(os.path.pardir)
os.chdir(os.path.pardir)

# Build NutCracker
os.chdir("sdmmlib")
os.chdir("nutcracker")
os.system("python setup.py build_ext --inplace")
os.chdir(os.path.pardir)
os.chdir(os.path.pardir)

print("Copying structures...")
shutil.copytree(os.path.join("sdmmlib", "dscstools", "DSCSTools", "DSCSTools", "structures"), 
                os.path.join(os.path.curdir, "structures"))
print("Setup complete.")
