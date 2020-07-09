#! /usr/bin/env python3
import logging

from ops.charm import CharmBase

from ops.framework import (
    StoredState,
    ObjectEvents,
    EventSource,
    EventBase,
)

from ops.main import main

from slurm_ops_manager import SlurmOpsManager

from slurmctld import SlurmctldRequirer

from interface_slurmd import SlurmdProvider

logger = logging.getLogger()


class SlurmdCharm(CharmBase):

    _state = StoredState()

    def __init__(self, *args):
        super().__init__(*args)

        self._state.set_default(controller_config=None)
        self._state.set_default(slurm_installed=False)
        self._state.set_default(controller_available=False)

        #interfaces
        self.slurmctld = SlurmctldRequirer(self, "slurmctld")
        self.slurmd_provider = SlurmdProvider(self, "slurmd")
        #instances
        self.slurm_manager = SlurmOpsManager(self, "slurmd")

        self.framework.observe(
            self.on.install,
            self._on_install
        )

        self.framework.observe(
            self.on.start,
            self._on_start
        )

        self.framework.observe(
            self.slurmctld.on.controller_available,
            self._on_controller_available
        )

    def _on_install(self, event):
        self.slurm_manager.prepare_system_for_slurm()
        self._state.slurm_installed = True

    def _on_controller_available(self, event):
        logger.debug("_______slurmd inventory available and writing______")
        logger.debug(self.slurmd_peer.get_slurmd_inventory())
        logger.debug(self.slurmctld.get_controller_config())

        ctxt = {
            # 'nodes': self.slurmd_provider,
            'controller_config': self.slurmctld.get_controller_config(),
        }

        self.slurm_manager.write_config(ctxt)
        self.slurm_manager._slurm_systemctl("start")


    def _on_start(self, event):
        #self.slurm_install_manager.slurm_component('start')
        pass


if __name__ == "__main__":
    main(SlurmdCharm)
