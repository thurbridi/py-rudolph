# Rudolph, The Renderer Reindeer :deer:
> Gladly, rudolph was bitten by a snake.

This is an Interative Computer Graphics System made for UFSC's INE5420 course, called "Computer Graphics".

**This is an experimental version of Rudolph written in Python.**

## setup.sh
Assuming you have pipenv, PyGObject and it's dependencies intalled in your linux distribution, you can run `setup.sh` to install the project's dependencies and run it via pipenv.

## Manual installation
### Setup
```
# pacman -S python cairo pkgconf gobject-introspection gtk3
$ pipenv install
$ pipenv shell
```


### Run
```
$ python src/main.py
```