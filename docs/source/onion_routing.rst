Integrated Onion Routing for Peer-to-Peer Validator Privacy in the Ethereum Network
===================================================================================

In this section, we introduce the API for the `Onion Routing based protocol <https://info.ilab.sztaki.hu/~kdomokos/OnionRoutingP2PEthereumPrivacy.pdf>`_ that we propose for P2P
validator privacy in the Ethereum Network.

Our Protocol
------------

The general idea of an onion routing scheme is similar to Dandelion-style schemes in that the message is relayed from the originator to the broadcaster through a number of hops. The main difference, however, is that the relayers forward the message encrypted, and only the broadcaster sees the message in plain-text. The originator encrypts the message using the public key of each relayer, and each relayer forwards the message by first unencrypting it using its private key. Successfully executed, onion routing has the potential to prevent any single party from linking the IP address and public key of the originator.

Currently, you can only specify the number of relayers that we sample uniformly at random from P2P network nodes to form one encrypted channel for each originator. Later, we plan to add the number of channels per originator as a new parameter.

.. autoclass:: ethp2psim.protocols.OnionRoutingProtocol

Onion Routing Adversary
-----------------------

In order to properly compare our approach with previous privacy-enhancing solutions (e.g, Dandelion(++)) we implemented an adversary that cannot differentiate between messages during the anonymity phase, when the messages are propagated in an ancrypted form from the originator towards the broadcaster.

You can initialize this adversary in an identical way to the formerly identified adversaries.

.. autoclass:: ethp2psim.adversary.OnionRoutingAdversary

Basically, the this adversary is constantly recording the timestamps of received and forwarded encrypted packages and tries to backtrack each channel from the broadcaster to the originator with the following functions.

.. autofunction:: ethp2psim.adversary.OnionRoutingAdversary.eavesdrop_msg

.. autofunction:: ethp2psim.adversary.OnionRoutingAdversary.record_packet

Finally, you can query the predicted originator for each message in a dataframe:

.. autofunction:: ethp2psim.adversary.OnionRoutingAdversary.predict_msg_source