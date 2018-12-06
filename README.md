# Item Catalog

This project is designed in accordance to specifications issued by the Udacity team for the "Backend: Databases & Applications" segment of their [Full Stack Web Development Nanodegree](https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd004).  It is an online application that creates a database, allows a user to login using 3rd party authorization through Google, edit, delete and create new categories and/or items within those categories, and outside unauthorized users can safely view items and categories without being able to damage them.

## Visit the Site!

[Item Catalog Site](http://www.item-catalog.com)

**Only works in Incognito mode currently.**

This app is officially hosted on it's own domain. It isn't pretty, but you can see the functionality of the login/logout and database logic in action.

## How To Use

1. In order to use this app, the user must first my have previously installed Git, Vagrant, and Virtual Box, in addition to having Python (preferably Python 3) on thier local machine.
2. Once the user has made these additions to their local machine, they must either set up a Vagrant virtual machine on their own, or they can alternatively clone [this repository](https://github.com/udacity/fullstack-nanodegree-vm).
4. Next clone this repository to your local machine inside the Vagrant directory either created or downloaded from the previously shown link.
3. The user then should get their Vagrant machine running by issuing first ```vagrant up``` from either the command line--Git or otherwise-- followed by ```vagrant ssh```.
4. In order to initialize the model, the user should first run ```python models.py``` followed by ```python views.py```
5. The user can now open the main page of the site by opening up their browser and routing to [http://localhost:8000/](http://localhost:8000/).

## Acknowledgements

Acknowledgements for this project go solely to the Udacity faculty who designed the curriculum necessary to put this project together, and to my family for supporting and encouraging me as I assembled it.
