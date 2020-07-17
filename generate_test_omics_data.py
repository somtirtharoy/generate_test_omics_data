
import cobra
import pandas as pd
import random
import os

data_file_path = 'data'

def generate_fake_data(model, condition):
    """

    :param model: cobra model object
    :param solution: solution for the model optimization using cobra
    :param data_type: defines the type of -omics data to generate (all by default)
    :return:
    """

    # reaction_id of choice passed to the function# hardcoded here for this particular file (Need to convert this to an interactive cli program)
    reaction_id = 'BIOMASS_Ec_iJO1366_core_53p95M'
    # solution = None

    while condition:
        print("Condition parameter: ", condition)
        condition-=1
        solution = get_optimized_solution(model, reaction_id)

        get_proteomics_transcriptomics_data(model, solution, condition)

        get_metabolomics_data(model, condition)



def get_metabolomics_data(model, condition):
    """

    :param model:
    :param condition:
    :return:
    """
    metabolomics = {}
    # get metabolites
    # NOTE: Need to find a better algorithm. This is O(n^3)
    for met in model.metabolites:
        # get associated reactions
        for reaction in list(met.reactions):
            # get dictionary of associated metabolites and their concentrations
            for metabolite, conc in reaction._metabolites.items():
                if metabolite.id == met.id:
                    # map the BIGG ids to CIDs using the inchikeys in the metabolites and the ampping file
                    # that we have generated from Pubchem
                    # remember that not all Inchikeys dont have a mappping to a CIDs and there are
                    # multiple mappings for some Inchikeys
                    if met.id not in metabolomics.keys():
                        metabolomics[met.id] = abs(conc)
                    else:
                        metabolomics[met.id] += abs(conc)
        # getting number of associated reactions and averaging the metabolic concentration value
        num_reactions = len(list(met.reactions))
        metabolomics[met.id]/=num_reactions

    metabolomics_dataframe = pd.DataFrame.from_dict(metabolomics, orient='index', columns=['metabolomics_value'])
    # Write the dataframe into a csv file
    file_name = f'{data_file_path}/metabolomics_fakedata_condition_{condition}.csv'
    write_data_files(metabolomics_dataframe, "metabolomics")



def get_proteomics_transcriptomics_data(model, solution, condition):
    """

    :param model:
    :param solution:
    :param condition:
    :return:
    """

    # pre-determined linear constant (NOTE: Allow user to set this via parameter)
    # DISCUSS!!
    k = 0.8
    q = 0.06

    proteomics = {}
    transcriptomics = {}
    fluxomics = {}

    rxnIDs = solution.fluxes.keys()
    for rxnId in rxnIDs:
        reaction = model.reactions.get_by_id(rxnId)
        for gene in list(reaction.genes):

            # this will ignore all the reactions that does not have the gene.annotation property
            # DISCUSS!!
            if gene.annotation:
                if 'uniprot' not in gene.annotation:
                    if 'goa' in gene.annotation:
                        protein_id = gene.annotation['goa']
                    else:
                        break
                else:
                    protein_id = gene.annotation['uniprot']

                # create proteomics dict
                # Adding noise which is 5% of the signal data. signal + signal*0.05 = signal*1.05
                proteomics[protein_id] = (solution.fluxes[rxnId]/k)*1.05
                fluxomics[rxnId] = solution.fluxes[rxnId]

            # create transcriptomics dict
            transcriptomics[gene.id] = (proteomics[protein_id]/q)*1.05


    file_name = f'{data_file_path}/proteomics_fakedata_condition_{condition}.csv'
    proteomics_dataframe = pd.DataFrame.from_dict(proteomics, orient='index', columns=['proteomics_value'])
    write_data_files(proteomics_dataframe, "proteomics")

    file_name = f'{data_file_path}/transcriptomics_fakedata_condition_{condition}.csv'
    transcriptomics_dataframe = pd.DataFrame.from_dict(transcriptomics, orient='index', columns=['transcriptomics_value'])
    write_data_files(transcriptomics_dataframe, "transcriptomics")

    file_name = f'{data_file_path}/fluxomics_fakedata_condition_{condition}.csv'
    fluxomics_dataframe = pd.DataFrame.from_dict(fluxomics, orient='index', columns=['fluxomics_value'])
    write_data_files(fluxomics_dataframe, "fluxomics")


def write_data_files(dataframe, data_type=None, condition=1, line_name='WT'):
    """

    :param dataframe:
    :param data_type:
    :param condition:
    :return:
    """

    # create the filenames
    experiment_description_file_name = f'{data_file_path}/experiment_description_file.csv'
    omics_file_name = f'{data_file_path}/{data_type}_fakedata_sample_{condition}.csv'

    #write experiment description file
    try:
        with open(experiment_description_file_name, 'w') as fh:
            fh.write(f'Line Name,Line Description, Part ID, Media, Shaking Speed, Starting OD, Culture Volume, Flask Volume, Growth Temperature, Replicate Count\n')
            fh.write(f"{line_name}, KEIO wild type, JPUB_001327, M9, 1, 0.1, 50, 200, 30, 1\n")
    except Exception as ex:
        print("Error in writing file!")
        print(ex)

    # create file number two: omics file
    # TODO: Need to change the units to actual relevant units
    unit_dict = { "fluxomics": 'g/L',\
            "proteomics": 'proteins/cell',\
            "transcriptomics": "FPKM",\
            "metabolomics": "mg/L"
            }

    try:
        with open(omics_file_name, 'w') as fh:
            # fh.write("Line Name, Measurement Type, Value, Units\n")
            # sample_name = f"Sample {condition}\n"
            # spaces = ' '*(len('Line Name,')-3)
            time = 0
            fh.write(f'Line Name,Measurement Type,Time,Value,Units\n')
            for index, series in dataframe.iteritems():
                for id, value in series.iteritems():
                    fh.write((f'{line_name},{id},{time},{value},{unit_dict[data_type]}\n'))

    except Exception as ex:
        print("Error in writing file!")
        print(ex)



def get_random_number():
    """

    :return:
    """
    random.seed(12312)
    return random.random()

def add_random_noise():
    """

    :return:
    """
    pass


def get_list_of_reactions(file_name):
    """

    :param file_name: Name of the model file (has to be xml for now)
    :return: None (prints the list of reactions that has mass in them)
    """

    # Load model¶depending on the kind of file (the file has to be xml)
    if file_name.endswith(".xml"):
        model = cobra.io.read_sbml_model(file_name)

    # Print out the reaction name and reaction id for all reactions related to BIOMASS production:
    print("List of reactions related to BIOMASS production:")
    for rxn in model.reactions:
        if rxn.name is not None and 'BIOMASS' in rxn.id:
            print("{}: {}".format(rxn.id, rxn.name))



def get_optimized_solution(model, reaction_id):
    """

    :param model:
    :param reaction_id:
    :return solution:
    """

    # fix the flux value to -15 as we have data for this constraint
    model.reactions.get_by_id(reaction_id).lower_bound = -15
    model.reactions.get_by_id(reaction_id).upper_bound = -15
    # print(model.reactions.get_by_id(reaction_id))

    print("Displaying the reaction bounds afterG constraining them:")
    print(model.reactions.get_by_id(reaction_id).bounds)

    solution = model.optimize()

    return solution


def read_model(file_name):
    """

    :param file_name:
    :return model:
    """

    # Load model¶depending on the kind of file
    if file_name.endswith(".xml"):
        model = cobra.io.read_sbml_model(file_name)
    elif file_name.endswith(".json"):
        model = cobra.io.load_json_model(file_name)

    return model



# TODO: Need to create a cli program that can be supplied with fielname and it will ask for reaction name
#  and run the code to genarate the test data

if __name__ == "__main__":
    # file_name = 'iJR904.json'

    # if data folder doesn't exist create it
    if not os.path.isdir(data_file_path):
        os.mkdir(data_file_path)


    # file_name = f"{data_file_path}/iECIAI39_1322.xml"
    file_name = f"{data_file_path}/iJO1366.xml"
    # reaction_id = 'EX_glc__D_e'

    # if file name doesn't exist throw error
    if not os.path.isfile(file_name):
        raise Exception("File not present in the data directory!")


    # spits out the list of reaction names related to BIOMASS production
    get_list_of_reactions(file_name)

    # read model
    model = read_model(file_name)

    # get fake proteomics data and write it to file
    # NOTE: (need to add type of file, only CSV for now)
    condition = 1
    generate_fake_data(model, condition)

