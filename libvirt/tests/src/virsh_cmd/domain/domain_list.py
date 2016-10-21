import re
import logging

from autotest.client.shared import error

from virttest import virsh
from virttest import libvirt_vm
from virttest import utils_libvirtd
from virttest.utils_test import libvirt


def run(test, params, env):
    """
    Test command: virsh list and it's options.

    1) Obtain the prarams
    2) Filt parameters according libvirtd's version
    3) Prepare libvirt's status.
    4) Execute list command.
    5) Result check.
    """
    vm_name = params.get("main_vm", "avocado-vt-vm1")

    conn  = params.get("connection", "qemu:///system")
    scope = params.get("scope", "")
    state = params.get("state", "")

    libvirtd = params.get("libvirtd", "on")

    # check the status of libvirtd
    if not utils_libvirtd.libvirtd_is_running():
        #raise error.TestFail("Libvirtd service is dead.")
        #raise error.TestNAError("Libvirtd service is dead.")
        logging.info("Libvirtd service is dead!")
        utils_libvirtd.libvirtd_start()

    # Some parameters are not supported on old libvirt, skip them.
    help_info = virsh.help("list").stdout.strip()
    if scope and not re.search(scope, help_info):
        raise error.TestNAError("Option: %s is not supported." % scope)
    if state and not re.search(state, help_info):
        raise error.TestNAError("Option: %s is not supported." % state)

    def check_result(res, state=None):
        if res.exit_status:
            msg = "run list failed with(%d)." % (res.status, res.stdout.strip())
            raise error.TestFail(msg);
        else:
            domlist_out = res.stdout
            # Regular expression for the below output
            # Id    Name                           State
            # ----------------------------------------------------
            # 2     fedora23                       running
            rg = re.compile(r"(\d+)\s+(\w+)\s+(\w+)")

            NumOfDoms = 0
            for line in domlist_out.split('\n'):
                match_obj = rg.search(line)
                if match_obj is not None:
                    NumOfDoms += 1;
            logging.info("NumOfDoms :%s" % NumOfDoms)
            return int(NumOfDoms)

    # run test case
    result = virsh.dom_list(scope, ignore_status=True, print_info=True)
    Doms1 = check_result(result, scope)

    result = virsh.dom_list(state, ignore_status=True, print_info=True)
    Doms2 = check_result(result, state)

    if scope is None:
        # active : start_vm = yes
        if state == "--state-running":
            if Doms1 <= 0:
                raise error.TestFail("No running vm the --state-running!")
            if Doms1 < Doms2:
                raise error.TestFail("the running vms more than active vms!")
        if state == "--state-paused" and Doms1 < Doms2:
            raise error.TestFail("the paused vms more than active vms!")
    if scope == "--inactive":
        # inactive : start_vm = no
        if state == "--state-shutoff":
            if Doms2 <= 0:
                raise error.TestFail("No shutoff vm with --state-shutoff!")
            if Doms1 < Doms2:
                raise error.TestFail("the shutoff vms more than inactive vms!")
    if scope == "--all":
        if Doms1 < Doms2:
            raise error.TestFail("the %s vms exceeded the maximum!")
