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
#include "CombineHarvester/CombineTools/interface/Systematics.h"
#include "CombineHarvester/CombineTools/interface/CardWriter.h"
#include "CombineHarvester/CombineTools/interface/CopyTools.h"
#include "CombineHarvester/CombineTools/interface/BinByBin.h"

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

//So far only mutau added for MSSM, need to copy over all the systematics for other channels 

  VString chns =
      {{"mt"},
      {"et"}};

  map<string, string> input_folders = {
      {"mt", "Wisconsin"},
      {"et", "Wisconsin"}
  };
  
  map<string, VString> bkg_procs;
  bkg_procs["mt"] = {"ZTT", "W", "QCD", "ZL", "ZJ", "TT", "VV"};
  
  VString sig_procs = {"ggH", "bbH"};
  
  map<string, Categories> cats;
  cats["mt_13TeV"] = {
      {1, "mt_inclusive"},
      {2, "mt_inclusivemtnotwoprong"}};
  
  cats["et_13TeV"] = {
      {1, "et_inclusive"},
      {2, "et_inclusivemtnotwoprong"}};


  auto masses = ch::MassesFromRange(
      "90-140:10,140-180:20,600,900,1000,1200,1500,2900,3200");

  for (auto chn : chns) {
    cb.AddObservations(
      {"*"}, {"htt"}, {"13TeV"}, {chn}, cats[chn+"_13TeV"]);
    cb.AddProcesses(
      {"*"}, {"htt"}, {"13TeV"}, {chn}, bkg_procs[chn], cats[chn+"_13TeV"], false);
    cb.AddProcesses(
      masses, {"htt"}, {"13TeV"}, {chn}, sig_procs, cats[chn+"_13TeV"], true);
  }


  using ch::syst::SystMap;
  using ch::syst::era;
  using ch::syst::bin_id;
  using ch::syst::process;  
  cb.cp().backgrounds()
      .AddSyst(cb, "lumi_$ERA", "lnN", SystMap<era>::init
      ({"13TeV"}, 1.046));
  cb.cp().signals()
      .AddSyst(cb, "lumi_$ERA", "lnN", SystMap<era>::init
      ({"13TeV"}, 1.046));

  cb.cp().process({"ggH"})
      .AddSyst(cb, "pdf_gg", "lnN", SystMap<>::init(1.1));


  cb.cp().process(ch::JoinStr({sig_procs, {"ZTT", "ZL", "ZJ","TT","VV","W","QCD"}}))
      .AddSyst(cb, "CMS_eff_m", "lnN", SystMap<>::init(1.03));

  cb.cp().process(ch::JoinStr({sig_procs, {"ZTT", "ZL", "ZJ","TT","VV","W","QCD"}}))
      .AddSyst(cb, "CMS_eff_tau", "lnN", SystMap<>::init(1.10));

  cb.cp().process({"ZTT"})
      .AddSyst(cb, "norm_dy", "lnN", SystMap<>::init(1.1));
  cb.cp().process({"DY"})
      .AddSyst(cb, "norm_dyother", "lnN", SystMap<>::init(1.1));
  cb.cp().process({"VV"})
      .AddSyst(cb, "norm_VV ", "lnN", SystMap<>::init(1.1));
  cb.cp().process({"TT"})
      .AddSyst(cb, "norm_tt ", "lnN", SystMap<>::init(1.2));



  cout << ">> Extracting histograms from input root files...\n";
  for (string chn : chns) {
    string file = aux_shapes + input_folders[chn] + "/htt_" + chn +
                  ".inputs-mssm-" + "13TeV" + ".root";
    cb.cp().channel({chn}).era({"13TeV"}).backgrounds().ExtractShapes(
        file, "$BIN/$PROCESS", "$BIN/$PROCESS_$SYSTEMATIC");
    cb.cp().channel({chn}).era({"13TeV"}).signals().ExtractShapes(
        file, "$BIN/$PROCESS$MASS", "$BIN/$PROCESS$MASS_$SYSTEMATIC");
  }
  
  map<string, VString> signal_types = {
    {"ggH", {"ggH"}},
    {"bbH", {"bbH"}}
  };

  
  cout << ">> Setting standardised bin names...\n";
  ch::SetStandardBinNames(cb);
  
  string folder = "output/mssm_cards/LIMITS";
  boost::filesystem::create_directories(folder);
  boost::filesystem::create_directories(folder + "/common");
  for (auto m : masses) {
    boost::filesystem::create_directories(folder + "/" + m);
  }

  for (string chn : chns) {
    TFile output((folder + "/common/htt_" + chn + ".input.root").c_str(),
                 "RECREATE");
    auto bins = cb.cp().channel({chn}).bin_set();
    for (auto b : bins) {
      for (auto m : masses) {
        cout << ">> Writing datacard for bin: " << b << " and mass: " << m
                  << "\r" << endl;
        cb.cp().channel({chn}).bin({b}).mass({m, "*"}).WriteDatacard(
            folder + "/" + m + "/" + b + ".txt", output);
      }
    }
    output.Close();
  }

  
  cout << "\n>> Done!\n";
}
