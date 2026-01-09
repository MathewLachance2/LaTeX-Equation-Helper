"use strict";

var QWebChannelMessageTypes = {
    signal: 1,
    propertyUpdate: 2,
    init: 3,
    idle: 4,
    debug: 5,
    invokeMethod: 6,
    connectToSignal: 7,
    disconnectFromSignal: 8,
    setProperty: 9,
    response: 10,
};

var QWebChannel = function (transport, initCallback) {
    if (typeof transport !== "object" || typeof transport.send !== "function") {
        console.error("The QWebChannel expects a transport object with a send function and onmessage callback property." +
            " Given is: transport: " + typeof (transport) + ", transport.send: " + typeof (transport.send));
        return;
    }

    var channel = this;
    this.transport = transport;

    this.send = function (data) {
        if (typeof (data) !== "string") {
            data = JSON.stringify(data);
        }
        channel.transport.send(data);
    }

    this.transport.onmessage = function (message) {
        var data = message.data;
        if (typeof data === "string") {
            data = JSON.parse(data);
        }
        switch (data.type) {
            case QWebChannelMessageTypes.signal:
                channel.handleSignal(data);
                break;
            case QWebChannelMessageTypes.response:
                channel.handleResponse(data);
                break;
            case QWebChannelMessageTypes.propertyUpdate:
                channel.handlePropertyUpdate(data);
                break;
            default:
                console.error("invalid message received:", message.data);
                break;
        }
    }

    this.execCallbacks = {};
    this.execId = 0;
    this.objects = {};

    this.handleSignal = function (message) {
        var object = channel.objects[message.object];
        if (object) {
            object.signalEmitted(message.signal, message.args);
        } else {
            console.warn("Unhandled signal: " + message.object + "::" + message.signal);
        }
    }

    this.handleResponse = function (message) {
        if (!message.id) {
            return;
        }
        channel.execCallbacks[message.id](message.data);
        delete channel.execCallbacks[message.id];
    }

    this.handlePropertyUpdate = function (message) {
        for (var i in message.data) {
            var data = message.data[i];
            var object = channel.objects[data.object];
            if (object) {
                object.propertyUpdate(data.signals, data.properties);
            } else {
                console.warn("Unhandled property update: " + data.object + "::" + data.signal);
            }
        }
        channel.execCallbacks[message.id](message.data);
        delete channel.execCallbacks[message.id];
    }

    this.debug = function (message) {
        channel.send({ type: QWebChannelMessageTypes.debug, data: message });
    };

    channel.exec = function (data, callback) {
        if (typeof (callback) === "function") {
            channel.execId++;
            channel.execCallbacks[channel.execId] = callback;
            data.id = channel.execId;
        }
        channel.send(data);
    }

    channel.objects = {};

    channel.handleInit = function (data) {
        for (var i in data) {
            var object = new QObject(i, data[i], channel);
            channel.objects[i] = object;
        }
        // now resolve signals/properties/methods
        for (var i in channel.objects) {
            channel.objects[i].unwrapProperties();
        }
        if (initCallback) {
            initCallback(channel);
        }
    };

    channel.exec({ type: QWebChannelMessageTypes.init }, function (data) {
        channel.handleInit(data);
    });
};

function QObject(name, data, webChannel) {
    this.__id__ = name;
    this.webChannel = webChannel;

    for (var i in data.methods) {
        var method = data.methods[i];
        this[method[0]] = this.generateMethod(method[0], method[1]);
    }

    for (var i in data.properties) {
        var property = data.properties[i];
        this[property[0]] = property[1];
    }

    for (var i in data.signals) {
        var signal = data.signals[i];
        this[signal[0]] = this.generateSignal(signal[0], signal[1], signal[2]);
    }

    this.__objectSignals__ = {};
    this.__propertyCache__ = {};
}

QObject.prototype.generateMethod = function (name, numArgs) {
    var object = this;
    return function () {
        var args = [];
        var callback = undefined;
        for (var i = 0; i < arguments.length; i++) {
            if (typeof arguments[i] === "function") {
                callback = arguments[i];
            } else {
                args.push(arguments[i]);
            }
        }
        object.webChannel.exec({
            "type": QWebChannelMessageTypes.invokeMethod,
            "object": object.__id__,
            "method": name,
            "args": args
        }, function (response) {
            if (response !== undefined) {
                var result = response;
                if (callback) {
                    callback(result);
                }
            }
        });
    };
};

QObject.prototype.unwrapProperties = function () {
    for (var propertyIdx in this.__propertyCache__) {
        this[this.__propertyCache__[propertyIdx][0]] = this.__propertyCache__[propertyIdx][1];
    }
};

QObject.prototype.propertyUpdate = function (signals, properties) {
    // update property cache
    for (var propertyIdx in properties) {
        var property = properties[propertyIdx];
        this[property[0]] = property[1];
    }

    this.unwrapProperties();

    // emit signals
    for (var signalName in signals) {
        var signal = this[signalName];
        if (signal) {
            signal(signals[signalName]);
        }
    }
};

QObject.prototype.generateSignal = function (name, isProperty, numArgs) {
    var object = this;

    var signal = function () {
        var args = [];
        for (var i = 0; i < arguments.length; i++) {
            args.push(arguments[i]);
        }
        var callback = object.__objectSignals__[name];
        if (callback) {
            callback.apply(object, args);
        }
    };

    signal.connect = function (callback) {
        if (typeof (callback) !== "function") {
            console.error("Bad callback given to connect to signal " + name);
            return;
        }

        object.__objectSignals__[name] = callback;

        if (!isProperty) {
            object.webChannel.exec({
                "type": QWebChannelMessageTypes.connectToSignal,
                "object": object.__objectSignals__[name] ? object.__id__ : undefined,
                "signal": name
            });
        }
    };

    signal.disconnect = function (callback) {
        delete object.__objectSignals__[name];
        if (!isProperty) {
            object.webChannel.exec({
                "type": QWebChannelMessageTypes.disconnectFromSignal,
                "object": object.__id__,
                "signal": name
            });
        }
    };

    return signal;
};
