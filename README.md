# Migration_Scripts
Python and Powershell scripts used for migration.

Python Scripts
These scripts are used to fetch data from gsuite.

SharedDriveCount.txt is used to fetch shared drive count and size using GAM tool run it as a .bat file after installing GAM tool.
ramaining GAM commands can be found at https://sites.google.com/view/gam--commands/home or https://github.com/GAM-team/GAM/wiki

DeleteDuplecateRows.py ans GetTEamDriveOrganizers.py are dependency scripts for "SharedDriveCount.txt"

Crosslinks_new.py is used to get whether a file is located in shared drive or personal drive, give url as input. change email to admin email in line 18 and keep the input url in column 7 in your input csv file.

ClassifyLinks.py  also does the same as above but it takes multiple columns with urls as inputs. change email to admin email in lines 17 and 51, and keep the input urls in columns 4,5,6 in your input csv file you. if you want more input columns use line 134 to add more.

for the above two files prepare the input file which would be from the migration report and place them in the same folder as the script and ruin the script. new columns will be added to the input csv file with the output.

File_Finder.py use this script to get the location of a file or multiple files in gsuite. the input file should have fileowner email in column 1, and file id in column 2. Nothing to change in the code.

PullUniquePermissionsReport_Latest.py is used to get all the files with unique permissions of a drive in a single or multiple users. just create an input file with emails of users without a header and run the script.
