# Continuous Integration
- Each time you push to the repo, the Continuous Integration pipeline will run
- This pipeline consists of creating the correct development environment, building your code, and running all tests
- This is an extensive pipeline so it might take some time to complete


## Protecting Master Branch
Navigate to your Repository:
Open your repository on GitHub.

Click on "Settings":
In the upper-right corner of your repository page, click on the "Settings" tab.

Select "Branches" in the left sidebar:
On the left sidebar, look for the "Branches" option and click on it.

Choose the Branch:
Under "Branch protection rules," select the branch you want to protect. In this case, choose the main branch.

Enable Branch Protection:``
Check the box that says "Protect this branch."

Configure Protection Settings:
You can configure various protection settings. Some common settings include:

Require pull request reviews before merging: This ensures that changes are reviewed before being merged.
Require status checks to pass before merging: This ensures that automated tests and checks are passing.
Require signed commits: This enforces that commits are signed with a verified signature.
Restrict Who Can Push:
You can further restrict who can push directly to the branch. You might want to limit this privilege to specific people or teams.

Save Changes:
Once you've configured the protection settings, scroll down and click on the "Save changes" button.

Now, your main branch is protected, and certain criteria must be met before changes can be pushed directly to it. Contributors will need to create pull requests, have their changes reviewed, and meet other specified criteria before the changes can be merged into the main branch.


## Kernel Gallery
`.github/workflows/kernel-gallery.yml` runs the kernels listed in `ci/kernel_gallery.yaml` on SimX and, on main, force-pushes the results to the orphan branch `kernel-gallery` for gridworkz.com to read. Each entry names a case in `ci/testcases/` (`category:id`), so a gallery kernel runs exactly the app, args, configs and shape that case defines, at a 1-cluster, 4-core device when the case sets no shape of its own (or at the gallery entry's own `shape`, for a kernel that needs a bigger device). The branch holds `results.json` (each kernel's command, status and `PERF: instrs/cycles/IPC` summary), `logs/` and the kernel sources under `src/`. Pull requests that change the gallery run it as a check and publish nothing.

To run it locally, from a configured build tree:
```bash
python3 ci/kernel_gallery.py /tmp/kernel-gallery                    # all kernels
python3 ci/kernel_gallery.py /tmp/kernel-gallery --only model_parity:vecadd
```
