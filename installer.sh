#!/bin/sh

homeDIR="$( pwd )"

echo "[Checking system dependencies]"
PKG_OK=$(dpkg-query -W -f='${Status}' autoconf 2>/dev/null | grep -c "ok installed")
if test $PKG_OK = "0" ; then
  echo "autoconf not found. Install it with sudo apt-get install autoconf."
  exit
fi
PKG_OK=$(dpkg-query -W -f='${Status}' libtool 2>/dev/null | grep -c "ok installed")
if test $PKG_OK = "0" ; then
  echo "libtool not found. Install it with sudo apt-get install libtool."
  exit
fi
PKG_OK=$(dpkg-query -W -f='${Status}' gzip 2>/dev/null | grep -c "ok installed")
if test $PKG_OK = "0" ; then
  echo "gzip not found. Install it with sudo apt-get install gzip."
  exit
fi




madgraph="MG5_aMC_v2.9.2.tar.gz"
URL=https://launchpad.net/mg5amcnlo/2.0/2.9.x/+download/$madgraph
echo -n "Install MadGraph (y/n)? "
read answer
if echo "$answer" | grep -iq "^y" ;then
	mkdir MG5;
	echo "[installer] getting MadGraph5"; wget $URL 2>/dev/null || curl -O $URL; tar -zxf $madgraph -C MG5 --strip-components 1;
	cd $homeDIR
	rm $madgraph;
	echo "[installer] replacing MadGraph files with fixes";
    cp ./madgraphfixes/mg5_configuration.txt MG5/input/;
    cp ./madgraphfixes/madgraph_interface.py MG5/madgraph/interface/;
    cp ./madgraphfixes/diagram_generation.py MG5/madgraph/core/;

fi

#Get pythia tarball (does not seem to work wiht pythia 8.3)
#pythia="pythia8303.tgz"
pythia="pythia8244.tgz"
URL=http://home.thep.lu.se/~torbjorn/pythia8/$pythia
echo -n "Install Pythia (y/n)? "
read answer
if echo "$answer" | grep -iq "^y" ;then
	if hash gzip 2>/dev/null; then
		mkdir pythia8;
		echo "[installer] getting Pythia"; wget $URL 2>/dev/null || curl -O $URL; 
        tar -zxf $pythia -C pythia8 --strip-components 1;
		echo "Installing Pythia in pythia8";
		cd pythia8;
		./configure --with-root=$ROOTSYS --prefix=$homeDIR/pythia8 --with-gzip
		make -j4; make install;
		cd $homeDIR
#		rm $pythia;
	else
		echo "[installer] gzip is required. Try to install it with sudo apt-get install gzip";
	fi
fi

#It does not seem to work with the latest Delphes release
echo -n "Install Delphes (y/n)? "
read answer
if echo "$answer" | grep -iq "^y" ;then
	echo "[installer] getting Delphes";
  git clone --branch 3.4.2 https://github.com/delphes/delphes.git Delphes;
  cd Delphes;
  export PYTHIA8=$homeDIR/pythia8;
  echo "[installer] installing Delphes";
  make HAS_PYTHIA8=true;
	cd $homeDIR;
fi


echo -n "Install CheckMATE (y/n)? "
read answer
if echo "$answer" | grep -iq "^y" ;then
  echo "[installer] -----> CheckMATE must be installed with python2 and a ROOT version compiled with python2!";
  echo "[installer] -----> Make sure ROOT_INCLUDE_PATH has been set and points to Delphes/external.";
  echo "[installer] -----> Make sure ROOTSYS points to a python2-compiled ROOT version.\n\n";
  echo "[installer] getting CheckMATE";
  git clone --branch v3.0beta git@github.com:CheckMATE2/checkmate2.git CheckMATE3;
  cd CheckMATE3;
  rm -rf .git
  autoreconf -i -f;
  ./configure --with-rootsys=$ROOTSYS --with-delphes=$homeDIR/Delphes --with-pythia=$homeDIR/pythia8 --with-madgraph=$homeDIR/MG5
  echo "[installer] installing CheckMATE";
  make -j4
  cd $homeDIR

fi
