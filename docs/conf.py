import cloud_sptheme as csp
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
source_suffix = '.rst'
master_doc = 'index'
project = u'git-spindle'
copyright = u'2012-2015, Dennis Kaarsemaker'
version = '3.0'
release = '3.0'
exclude_patterns = ['_build']
pygments_style = 'sphinx'
html_theme = 'cloud'
html_static_path = ['_static']
html_theme_options = {
    'roottarget': 'index',
    'stickysidebar': False,
}
html_theme_path = [csp.get_theme_dir()]
html_show_sourcelink = False
html_show_sphinx = False
extensions = ['ansicolor']
man_pages = [
    ('github', 'git-hub', 'GitHub integration', 'Dennis Kaarsemaker', '1'),
    ('gitlab', 'git-lab', 'GitLab integration', 'Dennis Kaarsemaker', '1'),
    ('bitbucket', 'git-bb', 'BitBucket integration', 'Dennis Kaarsemaker', '1'),
    ('bitbucket', 'git-bucket', 'BitBucket integration', 'Dennis Kaarsemaker', '1'),
]
