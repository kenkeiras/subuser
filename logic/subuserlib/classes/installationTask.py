#!/usr/bin/env python
# This file should be compatible with both Python 2 and 3.
# If it is not, please file a bug report.

"""
Implements functions involved in building/installing/updating subuser images.
"""

#external imports
import sys
#internal imports
import subuserlib.classes.installedImage
import subuserlib.verify
from subuserlib.classes.userOwnedObject import UserOwnedObject
import subuserlib.classes.exceptions as exceptions

class InstallationTask(UserOwnedObject):
  def __init__(self,user,subusersToBeUpdatedOrInstalled,checkForUpdatesExternally=False):
    UserOwnedObject.__init__(self,user)
    self.__subusersToBeUpdated = subusersToBeUpdatedOrInstalled
    self.__upToDateImageSources = set()
    self.__outOfDateImageSources = set()
    self.__outOfDateSubusers = None
    self.__subusersWhosImagesFailedToBuild = set()
    self.checkForUpdatesExternally = checkForUpdatesExternally

  def getOutOfDateSubusers(self):
    """
    Returns a list of subusers which are out of date or have no InstalledImage associated with them.
    """
    if self.__outOfDateSubusers is None:
      self.getUser().getRegistry().log("Checking if images need to be updated or installed...")
      self.__outOfDateSubusers = set()
      for subuser in self.__subusersToBeUpdated:
        try:
          if not (subuser.locked() and (subuser.getImageSource().getLatestInstalledImage() is not None)):
            self.getUser().getRegistry().log("Checking if subuser "+subuser.getName()+" is up to date.")
            for imageSource in getTargetLineage(subuser.getImageSource()):
              if imageSource in self.__upToDateImageSources:
                continue
              if imageSource in self.__outOfDateImageSources:
                upToDate = False
              else:
                upToDate = self.isUpToDate(imageSource)
              if upToDate:
                self.__upToDateImageSources.add(imageSource)
              else:
                self.__outOfDateImageSources.add(imageSource)
                self.__outOfDateSubusers.add(subuser)
                break
          if subuser.getImageId() is None:
            self.__outOfDateSubusers.add(subuser)
        except exceptions.ImageBuildException as e:
          try:
            self.getUser().getRegistry().log(unicode(e))
          except NameError: #Python3
            self.getUser().getRegistry().log(str(e))
          self.__subusersWhosImagesFailedToBuild.add(subuser)
    return self.__outOfDateSubusers

  def isUpToDate(self,imageSource):
    installedImage = imageSource.getLatestInstalledImage()
    if installedImage is None:
      return False
    if not installedImage.isDockerImageThere():
      return False
    targetLineage = getTargetLineage(imageSource)
    installedLineage = installedImage.getImageLineage()
    if not (len(targetLineage) == len(installedLineage)):
      return False
    sideBySideLineages = zip(installedLineage,targetLineage)
    for installed,target in sideBySideLineages:
      if target in self.__outOfDateImageSources:
        return False
      if not installed.getImageId() == target.getLatestInstalledImage().getImageId():
        return False
    if not installedImage.getImageSourceHash() == imageSource.getHash():
      return False
    if self.checkForUpdatesExternally and installedImage.checkForUpdates():
      return False
    return True

  def updateOutOfDateSubusers(self):
    """
    Install new images for those subusers which are out of date.
    """
    parent = None
    for subuser in self.getOutOfDateSubusers():
      try:
        for imageSource in getTargetLineage(subuser.getImageSource()):
          if imageSource in self.__upToDateImageSources:
            parent = imageSource.getLatestInstalledImage().getImageId()
          elif imageSource in self.__outOfDateImageSources:
            parent = installImage(imageSource,parent=parent)
            self.__outOfDateImageSources.remove(imageSource)
            self.__upToDateImageSources.add(imageSource)
          else:
            if not self.isUpToDate(imageSource):
              parent = installImage(imageSource,parent=parent)
            self.__upToDateImageSources.add(imageSource)
        if not subuser.getImageId() == parent:
          subuser.setImageId(parent)
          subuser.getUser().getRegistry().logChange("Installed new image <"+subuser.getImageId()+"> for subuser "+subuser.getName())
      except exceptions.ImageBuildException as e:
        try:
          self.getUser().getRegistry().log(unicode(e))
        except NameError: #Python3
          self.getUser().getRegistry().log(str(e))
        self.__subusersWhosImagesFailedToBuild.add(subuser)

  def getSubusersWhosImagesFailedToBuild(self):
    return self.__subusersWhosImagesFailedToBuild

def installImage(imageSource,parent=None):
  """
  Install a image by building the given ImageSource.
  Register the newly installed image in the user's InstalledImages list.
  Return the Id of the newly installedImage.
  """
  imageSource.getUser().getRegistry().logChange("Installing "+imageSource.getName()+" ...")
  imageId = imageSource.build(parent)
  imageSource.getUser().getInstalledImages()[imageId] = subuserlib.classes.installedImage.InstalledImage(imageSource.getUser(),imageId,imageSource.getName(),imageSource.getRepository().getName(),imageSource.getHash())
  imageSource.getUser().getInstalledImages().save()
  return imageId

def getTargetLineage(imageSource):
  """
  Return the lineage of the ImageSource, going from its base dependency up to itself.
  """
  sourceLineage = []
  while imageSource:
    sourceLineage.append(imageSource)
    imageSource = imageSource.getDependency()
  return list(reversed(sourceLineage))
