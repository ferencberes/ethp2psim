import networkx as nx
import numpy as np
import wget, os


class GoerliTestnet:
    """
    Network container for the Goerli Testnet

    Examples
    --------
    >>> goerli = GoerliTestnet()
    >>> goerli.graph.number_of_nodes()
    1355
    >>> goerli.graph.number_of_edges()
    19146
    """

    def __init__(self):
        filename = "goerliTopology.edgelist"
        if not os.path.exists(filename):
            url = (
                "https://info.ilab.sztaki.hu/~fberes/ethp2psim/goerliTopology.edgelist"
            )
            _ = wget.download(url)
        self.graph = nx.read_edgelist(filename)


class StakedEthereumDistribution:
    """
    Container for staked Ethereum values

    Examples
    --------
    >>> staked_eth = StakedEthereumDistribution()
    >>> len(staked_eth.weights)
    11000
    """

    def __init__(self):
        filename = "stakedEthereumDistribution.npy"
        if not os.path.exists(filename):
            url = "https://info.ilab.sztaki.hu/~fberes/ethp2psim/stakedEthereumDistribution.npy"
            _ = wget.download(url)
        weights = np.load(filename, allow_pickle=True)
        self.weights = weights / np.sum(weights)
