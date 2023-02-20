Contributions
=============

The future of privacy in Ethereum also depends on you! The design space of privacy-enhanced broadcast and routing algorithms is enormous. Can you design a more private broadcast or message routing algorithm? Do you have an adversarial strategy that can deanonymize message originators better than what is already added to the simulator? Then, feel free to contribute to our simulator! We intend this endeavor to develop into a community effort towards a more private Ethereum. 

We encourage the community to contribute to this simulator by proposing their privacy-enhanced message routing protocols. Feel free to open a PR or create an issue.

Below you find additional information on how to contribute to this repository.

Tests
-----

Before making new commits always make sure that the code works perfectly:
```bash
pytest --doctest-modules --cov
```
**Please, always write tests for new code sections to maintain high code coverage!**

Source code formatting
----------------------

In this project, we use the [black](https://github.com/psf/black) Python code formatter.
**Before each commit, please execute the following commands to maintain proper code formatting!**

```bash
black ethp2psim
black tests
black scripts
black *.ipynb
```

Documentation
-------------

If you would like to fix or extend the documentation for this project then first, install the related dependencies with the command below:
```bash
cd docs
pip install -r requirements.txt
```

Then, you can update code documentation locally with the following command:
```bash
cd docs
make html
```

A generated documentation resides in the `docs/build/html/` folder.

Submitting changes
------------------

Please send a [GitHub Pull Request to ethp2psim](https://github.com/ferencberes/ethp2psim/pull/new/master) with a clear list of what you've done (read more about [pull requests](http://help.github.com/pull-requests/)). Please make sure all of your commits are atomic (one feature per commit).

Always write a clear log message for your commits. One-line messages are fine for small changes, but bigger changes should look like this:

    $ git commit -m "A brief summary of the commit
    > 
    > A paragraph describing what changed and its impact."


Thanks,

Ferenc, István, Domokos