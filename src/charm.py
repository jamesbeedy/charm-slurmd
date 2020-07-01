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

from slurmd_inventory import SlurmdPeer

from slurm_install_manager import SlurmInstallManager

from slurmctld_requires import Slurmctld


logger = logging.getLogger()


class SlurmdCharm(CharmBase):

    _store = StoredState()

    on = SlurmConfigEvents()

    def __init__(self, *args):
        super().__init__(*args)

        self._store.set_default(controller_config=None)

        self.slurmctld = Slurmctld(self, "slurmctld")
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

    def _on_install(self, event):
        self.slurm_install_manager.prepare_system_for_slurm()

    def _on_slurmctld_available(self, event):
        self._store.controller_config = self.slurmctld.get_controller_config()

    def _on_slurmd_inventory_available(self, event):
        """Write slurm.conf when a peer joins the relation."""

        slurm_installed = self.slurm_install_manager.slurm_installed
        slurmctld_available = self.slurmctld.controller_config_available

        if not (slurm_installed and slurmctld_available):
            event.defer()
            return

        ctxt = {
            'inventory': self.slurmd_peer.get_slurmd_inventory(),
            'controller_config': self._store.controller_config,
        }

        self.slurm_install_manager.write_config(ctxt)
        self.slurm_install_manager.slurm_component("restart")

    def _on_start(self, event):
        self.snap_install_manager.start_slurm_component()


if __name__ == "__main__":
    main(SlurmdCharm)
