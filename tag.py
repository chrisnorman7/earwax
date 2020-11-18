"""Add a tag and upload."""

from datetime import datetime
from subprocess import call

if __name__ == "__main__":
    now: datetime = datetime.now()
    if call(['git', 'tag', now.strftime('%Y-%m-%d')]) == 0:
        print('Tag created.')
        if call(['git', 'push', '--tags']) == 0:
            print('Tag uploaded.')
            if call(['upload.bat']) == 0:
                print('Release uploaded.')
            else:
                print('Failed to upload release.')
        else:
            print('Failed to upload tag.')
    else:
        print('Failed to create tag.')
