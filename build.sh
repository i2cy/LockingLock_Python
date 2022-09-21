rm -rf i2llserver.egg-info
rm -rf build
mv dist/* history/
python3 -m build
