# Create __init__.py in each Python package
New-Item -Path backend\__init__.py -ItemType File
New-Item -Path backend\api\__init__.py -ItemType File
New-Item -Path backend\domain\__init__.py -ItemType File
New-Item -Path backend\workflow\__init__.py -ItemType File
New-Item -Path backend\services\__init__.py -ItemType File
New-Item -Path backend\validators\__init__.py -ItemType File
New-Item -Path evals\__init__.py -ItemType File
New-Item -Path tests\__init__.py -ItemType File
