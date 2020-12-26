"""Add a tag and upload."""

from argparse import ArgumentParser
from subprocess import call

parser: ArgumentParser = ArgumentParser()

parser.add_argument('version', help='The version number to use')

if __name__ == "__main__":
    args = parser.parse_args()
    if call(['git', 'tag', args.version]) == 0:
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
