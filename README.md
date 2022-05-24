# Urban Dictionary List

Script and sample dataset of all urban dictionary entries (around 2.7 million total):

```bash
$ head -1000 data/a.data | tail -20
A Classy rimjob
A Clayton
a clean cunt
a clean golf ball
A Clean Pinch
A Clean Rig
a clean sanchez
a clean sink
A clean slide
A clear bag of smashed assholes
a cleeb
a cleggy
a cliff
A clinker
A Clint Colvin
A clint song
A Clint Stevens
a clinton
a clip around the ear
a clip around the ear hole.
```


## Data
This repo includes a snapshot of all entry names from Urban dictionary taken in April 2022. The lists are found in [`data/`](https://github.com/mattbierner/urban-dictionary-word-list/tree/master/data) and are bucketed by starting letter.

Each entry name is on it's own line in the file.

## Script
The included Python script allows you to download entries directly in case you want to update the current snapshot.
It appends all new entries to the existing files by default.

```sh
# download all entries that start with 'a', 'b', or 'c'
# and appends to existing files
$ python main.py a b c --out "{0}.data"
```

```sh
# download and update all entries
$ python main.py --remove-dead
```

## Usage
For reseach purposes. I'm not affiliated with Urban Dictionary.