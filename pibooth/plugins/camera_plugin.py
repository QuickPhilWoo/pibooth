# -*- coding: utf-8 -*-

import os
import os.path as osp
import time
import pygame
import pibooth
from pibooth.utils import LOGGER, timeit


class CameraPlugin(object):

    """Plugin to manage the camera captures.
    """

    def __init__(self, plugin_manager):
        self._pm = plugin_manager
        self.count = 0

    @pibooth.hookimpl
    def pibooth_cleanup(self, app):
        app.camera.quit()

    @pibooth.hookimpl
    def state_failsafe_enter(self, app):
        """Reset variables set in this plugin.
        """
        app.dirname = None
        app.capture_nbr = None
        app.camera.drop_captures()  # Flush previous captures

    @pibooth.hookimpl
    def state_wait_enter(self, app):
        app.dirname = None
        app.capture_nbr = None

    @pibooth.hookimpl
    def state_choose_do(self, app, events):
        event = app.find_choice_event(events)
        if event:
            if event.key == pygame.K_LEFT:
                app.capture_nbr = app.capture_choices[0]
            elif event.key == pygame.K_RIGHT:
                app.capture_nbr = app.capture_choices[1]

    @pibooth.hookimpl
    def state_preview_enter(self, cfg, app, win):
        LOGGER.info("Take a new capture")
        if not app.capture_nbr:
            app.capture_nbr = app.capture_choices[0]
        if not app.dirname:
            savedir = cfg.getpath('GENERAL', 'directory')
            app.dirname = osp.join(savedir, "raw", time.strftime("%Y-%m-%d-%H-%M-%S"))
            os.makedirs(app.dirname)
        app.camera.preview(win)

    @pibooth.hookimpl
    def state_preview_do(self, cfg, app):
        pygame.event.pump()  # Before blocking actions
        if cfg.getboolean('WINDOW', 'preview_countdown'):
            app.camera.preview_countdown(cfg.getint('WINDOW', 'preview_delay'))
        else:
            app.camera.preview_wait(cfg.getint('WINDOW', 'preview_delay'))

    @pibooth.hookimpl
    def state_preview_exit(self, cfg, app):
        if cfg.getboolean('WINDOW', 'preview_stop_on_capture'):
            app.camera.stop_preview()

    @pibooth.hookimpl
    def state_capture_do(self, cfg, app, win):
        capture_path = osp.join(app.dirname, "pibooth{:03}.jpg".format(self.count))
        effects = cfg.gettyped('PICTURE', 'captures_effects')
        if not isinstance(effects, (list, tuple)):
            # Same effect for all captures
            effect = effects
        elif len(effects) >= app.capture_nbr:
            # Take the effect corresponding to the current capture
            effect = effects[self.count]
        else:
            # Not possible
            raise ValueError("Not enough effects defined for {} captures {}".format(
                app.capture_nbr, effects))

        with timeit("Take a capture and save it in {}".format(capture_path)):
            if cfg.getboolean('WINDOW', 'flash'):
                with win.flash(2):  # Manage the window here, have no choice
                    app.camera.capture(capture_path, effect)
            else:
                app.camera.capture(capture_path, effect)

        self.count += 1

    @pibooth.hookimpl
    def state_capture_exit(self, cfg, app):
        if not cfg.getboolean('WINDOW', 'preview_stop_on_capture'):
            app.camera.stop_preview()
