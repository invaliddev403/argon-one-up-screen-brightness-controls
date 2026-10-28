import Gio from 'gi://Gio';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

const IFACE = `<node><interface name="local.argononeup.DdcBrightness">
<method name="Show"><arg type="u" direction="in" name="percent"/></method>
</interface></node>`;

export default class DdcBrightnessOverlay extends Extension {
    enable() {
        this._object = Gio.DBusExportedObject.wrapJSObject(IFACE, {
            Show(percent) {
                const level = Math.min(100, percent);
                Main.osdWindowManager.showAll(
                    Gio.ThemedIcon.new('display-brightness-symbolic'),
                    `Brightness ${level}%`, level / 100, 1);
            },
        });
        this._object.export(Gio.DBus.session, '/local/argononeup/DdcBrightness');
    }

    disable() {
        this._object?.unexport();
        this._object = null;
    }
}
