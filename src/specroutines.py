"""
specroutines.py

    The file with functions to connect and manipulate SpecMod objects 
    for use with Dash.
"""
import numpy as np
from SpecMod.specmod.Spectral import Spectra

def format_spectra_path(pdir, ev):
    return f"{pdir}/{ev}/Spectra/{ev}.spec"


def get_event_spectra(pdir: str, ev: str) -> Spectra:
    """
    Loads in the spectra for a given local specmod event spectra group
    for a given event (datetime string).

    Args:
        pdir (str): The parent directory of the specmod spectra pickle file
        ev (str): The event datetime (e.g., "2012-10-08T12:12:12.760000Z")

    Returns:
        tr (specmod.Spectra): A SpecMod spectral instance
    """
    sp = Spectra.read_spectra(
        format_spectra_path(
            pdir, ev), 
        skip_warning=True, method='pickle')
    return sp


def write_specs(pdir: str, data: dict) -> None:
    """
    Writes the spectra for a given local specmod event spectra group
    for a given event.

    Args:
        pdir (str): The parent directory of the specmod spectra pickle file
        ev (str): The event datetime (e.g., "2012-10-08T12:12:12.760000Z")
        data (dict): A dict containing the metadata from specmod dash.

    Returns:
        None
    """

    # iterate over the values in data which are the ones that have been ...
    # inspected and possibly changed. 
    for ev, stas in data.items():

        sp = get_event_spectra(pdir, ev)
        
        for sta, meta in stas.items():

            snp = sp.get_spectra(sta)
            
            # print(sta, meta['snr'], snp.signal.get_pass_snr())

            snp.signal.set_pass_snr(meta["snr"])

            # print(sta, meta['snr'], snp.signal.get_pass_snr())
            # if it can be modeled it should also have a bandwidth to set
            if meta["snr"]:
                snp.ubfreqs = np.array([10**meta["min bf"], 10**meta["max bf"]])
            # if it can't be modeled then I set ubfreqs to an empty array in SpecMod
            if not meta["snr"]:
                snp.ubfreqs = np.array([])


        sp.write_spectra(format_spectra_path(pdir, ev), sp, method='pickle')
        print(f"wrote {ev} to file at {format_spectra_path(pdir, ev)}")
