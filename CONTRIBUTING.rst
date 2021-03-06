.. highlight:: shell

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/sjoerdk/anonapi/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

AnonAPI could always use more documentation, whether as part of the
official AnonAPI docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/sjoerdk/anonapi/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `anonapi` for local development.

1. Fork the `anonapi` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/anonapi.git

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development::

    $ mkvirtualenv anonapi
    $ cd anonapi/
    $ python setup.py develop

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass flake8 and the
   tests, including testing other Python versions with tox::

    $ flake8 anonapi tests
    $ python setup.py test or py.test
    $ tox

   To get flake8 and tox, just pip install them into your virtualenv.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for Python 3.4, 3.5 and 3.6, and for PyPy. Check
   https://travis-ci.org/sjoerdk/anonapi/pull_requests
   and make sure that the tests pass for all supported Python versions.

Tips
----

To run a subset of tests::

$ py.test tests.test_anonapi


Deploying
---------

A reminder for the maintainers on how to deploy. General steps for a full deploy:

    * Check in all your changes locally
    * Make sure all test run and coverage is 90% or better
    * Push to master
    * update changelog (see below)

Checking in code
~~~~~~~~~~~~~~~~
Make sure all your changes are committed and all tests run. Make sure coverage is 90% or better
Then run::

$ bumpversion patch # possible: major / minor / patch (use semantic versioning https://semver.org/)
$ git push
$ git push --tags

Updating the changelog
~~~~~~~~~~~~~~~~~~~~~~
anonapi auto-generates change logs from github issues using
https://github.com/github-changelog-generator/github-changelog-generator

General points about working with this generator:

    * Label github issues with 'bug', 'enhancement' to make them show up better in the overview
    * To add summary information to the changelog for any version, see here: https://github.com/github-changelog-generator/github-changelog-generator#using-the-summary-section-feature

To re-generate, run:

    $ github_changelog_generator -u sjoerdk -p anonapi --token <your token>

To get a github token, see here: https://github.com/github-changelog-generator/github-changelog-generator#github-token

Updating docs
~~~~~~~~~~~~~
CI will generate and publish sphinx docs on readthedocs for tagged commits. Updating the sphinx docs in `/docs/sphinx`
will be enough in many cases. Some parts of the sphinx documentation are generated. In particular the `concepts.rst` and
`command_reference.rst` pages contain lists of all CLI commands that are generated from the CLI code directly.
To re-generate these, run

   `/docs/generator/generate_command_reference.rst.py`

