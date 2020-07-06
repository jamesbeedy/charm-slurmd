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

from slurmd_peer import SlurmdPeer

from slurm_install_manager import SlurmInstallManager

from slurmctld import SlurmctldRequirer


logger = logging.getLogger()


class SlurmdCharm(CharmBase):

    _state = StoredState()

    def __init__(self, *args):
        super().__init__(*args)

        self._state.set_default(controller_config=None)
        self._state.set_default(controller_available=False)

        self.slurmctld = SlurmctldRequirer(self, "slurmctld")
        self.slurmd_peer = SlurmdPeer(self, "slurmd-peer")

        self.slurm_install_manager = SlurmInstallManager(
            self,
            'slurmd',
        )

        self.framework.observe(
            self.on.install,
            self._on_install
        )
        self.framework.observe(
            self.on.start,
            self._on_start
        )

        self.framework.observe(
            self.slurmd_peer.on.slurmd_inventory_available,
            self._on_slurmd_inventory_available
        )

        self.framework.observe(
            self.slurmctld.on.controller_available,
            self._on_controller_available
        )

    def _on_install(self, event):
        self.slurm_install_manager.prepare_system_for_slurm()

    def _on_controller_available(self, event):
        logger.debug("_______slurmd inventory available and writing______")
        logger.debug(self.slurmd_peer.get_slurmd_inventory())
        logger.debug(self.slurmctld.get_controller_config())

        ctxt = {
            'nodes': self.slurmd_peer.get_slurmd_inventory(),
            'controller_config': self.slurmctld.get_controller_config(),
        }

        self.slurm_install_manager.write_config(ctxt)
        self.slurm_install_manager.slurm_systemctl("restart")

    def _on_slurmd_inventory_available(self, event):
        """Write slurm.conf when a peer joins the relation."""



    def _on_start(self, event):
        #self.slurm_install_manager.slurm_component('start')
        pass


if __name__ == "__main__":
    main(SlurmdCharm)
