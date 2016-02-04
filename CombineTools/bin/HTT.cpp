#include <string>
#include <map>
#include <set>
#include <iostream>
#include <vector>
#include <utility>
#include <cstdlib>
#include "boost/filesystem.hpp"
#include "CombineHarvester/CombineTools/interface/CombineHarvester.h"
#include "CombineHarvester/CombineTools/interface/Utilities.h"
#include "CombineHarvester/CombineTools/interface/CardWriter.h"
#include "CombineHarvester/CombineTools/interface/CopyTools.h"
#include "CombineHarvester/CombineTools/interface/BinByBin.h"
#include "CombineHarvester/CombineTools/interface/Systematics.h"

using namespace std;

int main() {
  ch::CombineHarvester cb;

  typedef vector<pair<int, string>> Categories;
  typedef vector<string> VString;

  string auxiliaries  = string(getenv("CMSSW_BASE")) + "/src/auxiliaries/";
  string aux_shapes   = auxiliaries +"shapes/";
  string aux_pruning  = auxiliaries +"pruning/";
  string input_dir =
      string(getenv("CMSSW_BASE")) + "/src/CombineHarvester/CombineTools/input";

  VString chns =
      {"et", "mt"};

  map<string, string> input_folders = {
      {"et", "Wisconsin"},
      {"mt", "Wisconsin"},
  };

  map<string, VString> bkg_procs;
  bkg_procs["et"] = {"ZTT", "W", "QCD", "ZL", "ZJ", "TT", "VV"};
  bkg_procs["mt"] = {"ZTT", "W", "QCD", "ZL", "ZJ", "TT", "VV"};

  VString sig_procs = {"ggH", "bbH"};

  map<string, Categories> cats;

  cats["et_13TeV"] = {
      {1, "et_inclusive"},
      {2, "et_inclusivemtnotwoprong"}};


  cats["mt_13TeV"] = {
      {1, "mt_inclusive"},
      {2, "mt_inclusivemtnotwoprong"}};


  cout << ">> Creating Many Mass points ...\n";
  //vector<string> masses = ch::ValsFromRange("125");
  //auto masses = ch::MassesFromRange(
  //    "90-140:10,140-180:20,250,400-500:50,600,700,900,1000-1200:200");
  vector<string> masses = {"80", "90", "100", "110", "120", "130", "140", "160", "180", "600", "900", "1000", "1200", "1500", "2900", "3200"};

  cout << ">> Creating processes and observations just for 13 TeV...\n";
  for (string era : { "13TeV"}) {
    for (auto chn : chns) {
      cb.AddObservations(
        {"*"}, {"htt"}, {era}, {chn}, cats[chn+"_"+era]);
      cb.AddProcesses(
        {"*"}, {"htt"}, {era}, {chn}, bkg_procs[chn], cats[chn+"_"+era], false);
      cb.AddProcesses(
        masses, {"htt"}, {era}, {chn}, sig_procs, cats[chn+"_"+era], true);
    }
  }
  //// Have to drop ZL from tautau_vbf category
  //cb.FilterProcs([](ch::Process const* p) {
  // return p->bin() == "tauTau_vbf" && p->process() == "ZL";
  //});

  cout << ">> Adding systematic uncertainties...\n";

  //Some of the code for this is in a nested namespace, so
  // we'll make some using declarations first to simplify things a bit.
  using ch::syst::SystMap;
  using ch::syst::era;
  using ch::syst::bin_id;
  using ch::syst::process;


  //! [part5]
  cb.cp().signals()
	  .AddSyst(cb, "lumi_$ERA", "lnN", SystMap<era>::init
			  ({"13TeV"}, 1.06));
  //! [part5]
  cb.cp().backgrounds()
	  .AddSyst(cb, "lumi_$ERA", "lnN", SystMap<era>::init
			  ({"13TeV"}, 1.06));
 
  //! [part6]

  cb.cp().process(ch::JoinStr({sig_procs, {"ZTT", "TT","ZL","ZJ","W"}}))
	  .AddSyst(cb, "CMS_eff_m", "lnN", SystMap<>::init(1.02));


  cb.cp().process(ch::JoinStr({sig_procs, {"ZTT", "TT","ZL","ZJ", "QCD","W"}}))
	  .AddSyst(cb, "CMS_eff_t", "lnN", SystMap<>::init(1.06));




  cout << ">> Extracting histograms from input root files for 13 TeV...\n";
  //for (string era : {"7TeV", "8TeV", "13TeV"}) {
  for (string era : { "13TeV"}) {
	  for (string chn : chns) {
		  // Skip 7TeV tt:
		  string file = aux_shapes + input_folders[chn] + "/htt_" + chn +
			  ".inputs-mssm-" + era + ".root";
		  cout<<"File to extract: "<< file <<endl;
		  cb.cp().channel({chn}).era({era}).backgrounds().ExtractShapes(
				  file, "$BIN/$PROCESS", "$BIN/$PROCESS_$SYSTEMATIC");
		  cb.cp().channel({chn}).era({era}).signals().ExtractShapes(
				  file, "$BIN/$PROCESS$MASS", "$BIN/$PROCESS$MASS_$SYSTEMATIC");
	  }
  }


  cout << ">> Merging bin errors and generating bbb uncertainties...\n";

  auto bbb = ch::BinByBinFactory()
	  .SetAddThreshold(0.1)
	  .SetMergeThreshold(0.5)
	  .SetFixNorm(true);

  ch::CombineHarvester cb_et = cb.cp().channel({"et"});
  bbb.MergeAndAdd(cb_et.cp().era({"13TeV"}).bin_id({1, 2}).process({"ZL", "ZJ", "QCD", "W"}), cb);
  bbb.MergeAndAdd(cb_et.cp().era({"13TeV"}).bin_id({3, 5}).process({"W"}), cb);
  bbb.MergeAndAdd(cb_et.cp().era({"13TeV"}).bin_id({6}).process({"ZL", "ZJ", "W"}), cb);
  bbb.MergeAndAdd(cb_et.cp().era({"13TeV"}).bin_id({7}).process({"ZL", "ZJ", "W", "ZTT"}), cb);

  ch::CombineHarvester cb_mt = cb.cp().channel({"mt"});
  bbb.MergeAndAdd(cb_mt.cp().era({"13TeV"}).bin_id({1, 2, 3, 4}).process({"W", "QCD"}), cb);
  bbb.MergeAndAdd(cb_mt.cp().era({"13TeV"}).bin_id({5, 6}).process({"W"}), cb);
  bbb.MergeAndAdd(cb_mt.cp().era({"13TeV"}).bin_id({7}).process({"W", "ZTT"}), cb);


  cout << ">> Setting standardised bin names...\n";
  //ch::SetStandardBinNames(cb);

  // The following is an example of duplicating existing objects and modifying
  // them in the process. Here we clone all mH=125 signals, adding "_SM125" to
  // the process name, switching it to background and giving it the generic mass
  // label. This would let us create a datacard for doing a second Higgs search

  // ch::CloneProcsAndSysts(cb.cp().signals().mass({"125"}), cb,
  //                        [](ch::Object* p) {
  //   p->set_process(p->process() + "_SM125");
  //   p->set_signal(false);
  //   p->set_mass("*");
  // });

  string folder = "MINE";
  boost::filesystem::create_directories(folder);
  boost::filesystem::create_directories(folder + "/common");
  for (auto m : masses) {
	  boost::filesystem::create_directories(folder + "/" + m);
  }

  for (string era : { "13TeV"}) {
	  for (string chn : chns) {
		  TFile output((folder + "/common/htt_" + chn + ".inputs-mssm" + era + ".root").c_str(),
				  "RECREATE");
		  auto bins = cb.cp().channel({chn}).bin_set();
		  for (auto b : bins) {
			  for (auto m : masses) {
				  cout << ">> Writing datacard for bin: " << b << " and mass: " << m
					  << "\r" << flush;
				  cb.cp().channel({chn}).bin({b}).mass({m, "*"}).WriteDatacard(
						  folder + "/" + m + "/" + b + ".txt", output);
			  }
		  }
		  output.Close();
	  }
  }

  /*
     Alternatively use the ch::CardWriter class to automate the datacard writing.
     This makes it simple to re-produce the LIMITS directory format employed during
     the Run I analyses.
     Uncomment the code below to test:
     */

  /*
  // Here we define a CardWriter with a template for how the text datacard
  // and the root files should be named.
  ch::CardWriter writer("$TAG/$MASS/$ANALYSIS_$CHANNEL_$BINID_$ERA.txt",
  "$TAG/common/$ANALYSIS_$CHANNEL.input_$ERA.root");
  writer.SetVerbosity(1);
  writer.WriteCards("output/sm_cards/LIMITS/cmb", cb);
  for (auto chn : cb.channel_set()) {
  writer.WriteCards("output/sm_cards/LIMITS/" + chn, cb.cp().channel({chn}));
  }
  */
  cout << "\n>> Done!\n";
}
