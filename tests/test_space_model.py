import os
import unittest

from anytree import Resolver

from nndt.space.abstracts import *
from nndt.space.loaders import *
from nndt.space.regions import *
from nndt.space.repr_mesh import *
from nndt.space.repr_sdt import *
from nndt.space.sources import *
from nndt.space.utils import *
from nndt.space.vtk_wrappers import *

class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, True)  # add assertion here

    def setUp(self):
        self.name_list = os.listdir('./acdc_for_test')
        self.name_list = [filename[:10] for filename in self.name_list if 'patient' in filename]
        self.name_list.sort()
        self.mesh_list = [f"./acdc_for_test/{p}/colored.obj" for p in self.name_list]
        self.sdt_list = [f"./acdc_for_test/{p}/sdf.npy" for p in self.name_list]

    def test_create_tree(self):

        space = Space("_main")
        group = Group("_default", parent=space)
        for ind, name in enumerate(self.name_list):
            object = Object(name, parent=group)
            mesh_source = MeshSource("mesh", self.mesh_list[ind], parent=object)
            sdt_source = SDTSource("sdt", self.sdt_list[ind], parent=object)

        self.assertTrue(space.is_root)
        self.assertEqual(5, len(group.children))

        print(object.children)
        print(object.explore())

    def test_function_load_data(self):
        space = load_data(self.name_list, self.mesh_list, self.sdt_list)

        self.assertTrue(space.is_root)
        print(space.explore())

        r = Resolver('name')
        obj = r.get(space, "default/patient009")
        self.assertEqual(2, len(obj.children))

    def test_ExtendedNodeMixin(self):
        space = load_data(self.name_list, self.mesh_list, self.sdt_list)

        self.assertTrue(space.is_root)
        self.assertEqual(5, len(space["default/"].children))
        self.assertEqual(2, len(space["default/patient009"].children))
        print(space.explore())

    def test_load_meshes(self):
        space = load_data(self.name_list, self.mesh_list, self.sdt_list)

        preload_all_possible(space)
        print(RenderTree(space))

        self.assertTrue(onp.allclose((((-0.9467665481567383, -0.9056295013427734, -0.9056295013427734),
                                       (0.9467665481567383, 0.9056295013427734, 0.9056295013427734))),
                                    space["default/patient009/mesh/repr"]._bbox, rtol=0., atol=1.e-2
                                    ))
        self.assertTrue(onp.allclose(((-0.9467665481567383, -0.9056295013427734, -0.9056295013427734),
                                      (0.9467665481567383, 0.9056295013427734, 0.9056295013427734)),
                                    space["default/patient009"]._bbox, rtol=0., atol=1.e-2
                                    ))
        self.assertTrue(onp.allclose(((-0.9522853851318359, -0.96994, -0.96994),
                                      (0.9522853851318359, 0.9699400000000002, 0.9699400000000002)),
                                    space["default"]._bbox, rtol=0., atol=1.e-2
                                    ))
        self.assertTrue(onp.allclose(((-0.9522853851318359, -0.96994, -0.96994),
                                      (0.9522853851318359, 0.9699400000000002, 0.9699400000000002)),
                                    space._bbox, rtol=0., atol=1.e-2
                                    ))

    def test_sampling_from_bbox(self):
        space = load_data(self.name_list, self.mesh_list, self.sdt_list)
        preload_all_possible(space)
        print(space.explore())

        sampling = space["default/patient009/mesh/repr/sampling_grid"](spacing=(2,2,2))
        self.assertEqual((2,2,2,3), sampling.shape)
        self.assertAlmostEqual(-0.9467, float(sampling.min()), places=2)
        self.assertAlmostEqual(0.9467, float(sampling.max()), places=2)

        sampling = space["default/patient009/sampling_grid"](spacing=(2,2,2))
        self.assertEqual((2,2,2,3), sampling.shape)
        self.assertAlmostEqual(-0.9467, float(sampling.min()), places=2)
        self.assertAlmostEqual(0.9467, float(sampling.max()), places=2)

        sampling = space["default/sampling_grid"](spacing=(2,2,2))
        self.assertEqual((2,2,2,3), sampling.shape)
        self.assertAlmostEqual(-0.9699, float(sampling.min()), places=2)
        self.assertAlmostEqual(0.9699, float(sampling.max()), places=2)

        sampling = space["sampling_grid"](spacing=(2,2,2))
        self.assertEqual((2,2,2,3), sampling.shape)
        self.assertAlmostEqual(-0.9699, float(sampling.min()), places=2)
        self.assertAlmostEqual(0.9699, float(sampling.max()), places=2)

    def test_sampling_eachN(self):
        space = load_data(self.name_list, self.mesh_list, self.sdt_list)
        preload_all_possible(space)
        print(space.explore())

        index_set, array = space["default/patient009/mesh/repr/sampling_eachN"](count=3, step=1, shift=0)
        self.assertEqual(0, index_set[0])
        self.assertEqual(1, index_set[1])
        self.assertEqual(2, index_set[2])

    def test_mesh_and_sdt_representation_are_comparable(self):
        space = load_data(self.name_list, self.mesh_list, self.sdt_list)
        preload_all_possible(space)
        print(RenderTree(space))

        max_errors = []
        for patient in self.name_list:
            bbox1 = space[f"default/{patient}/mesh/repr"]._bbox
            bbox2 = space[f"default/{patient}/sdt/repr"]._bbox
            self.assertTrue(onp.allclose(bbox1, bbox2, rtol=0., atol=0.009815))
            max_errors.append(onp.abs(onp.array(bbox1) - onp.array(bbox2)))
        print(onp.max(max_errors))

    def test_train_test_split(self):
        space = load_data(self.name_list, self.mesh_list, self.sdt_list, test_size=0.5)
        preload_all_possible(space)
        print(space.explore())

        self.assertIsNotNone(space["train/"])
        self.assertIsNotNone(space["test/"])

        test_list = range(len([ind ** 2 for ind in range(10)]))
        rng_1 = random.PRNGKey(0)
        test_size = 0.3

        index_train_1, index_test_1 = train_test_split(test_list,
                                                       rng=rng_1,
                                                       test_size=test_size)

        self.assertEqual(len(index_test_1) / len(test_list), test_size)
        self.assertEqual(len(index_train_1) / len(test_list), (1 - test_size))

        rng_2 = random.PRNGKey(1)
        index_train_2, index_test_2 = train_test_split(test_list,
                                                       rng=rng_2,
                                                       test_size=test_size)
        self.assertNotEqual(index_test_1, index_test_2)
        self.assertNotEqual(index_train_1, index_train_2)

    def test_colors(self):
        space = load_data(self.name_list, self.mesh_list, self.sdt_list)
        preload_all_possible(space)
        print(space.explore())

        self.assertIsNotNone(space["default/patient009/mesh/repr/point_color"])

        alpha = space["default/patient009/mesh/repr/point_color"].alpha
        points = space["default/patient009/mesh/repr"].surface_mesh2.mesh.GetNumberOfPoints()
        self.assertTrue(onp.allclose(onp.ones(points), alpha))


    def test_xyz2local_sdt(self):
        space = load_data(self.name_list, self.mesh_list, self.sdt_list)
        preload_all_possible(space)
        print(space.explore())

        self.assertIsNotNone(space["default/patient009/sdt/repr/xyz2local_sdt"])

        local, sdt = space["default/patient009/sdt/repr/xyz2local_sdt"]((0.,0.,0.), spacing=(5,5,5), scale=10)
        self.assertEqual((5,5,5,3), local.shape)
        self.assertEqual(-5, local.min())
        self.assertEqual(5, local.max())
        self.assertEqual((5,5,5,1), sdt.shape)

    def test_save_mesh(self):
        space = load_data(self.name_list, self.mesh_list, self.sdt_list)
        preload_all_possible(space)
        print(space.explore())

        num_points = space["default/patient009/mesh/repr"].surface_mesh2.mesh.GetNumberOfPoints()
        method = space["default/patient009/mesh/repr/save_mesh"]
        method('./result.vtp', {"ones": onp.ones(num_points), "zeros": onp.zeros(num_points)})

    def test_sampling_uniform(self):
        space = load_data(self.name_list, self.mesh_list, self.sdt_list)
        preload_all_possible(space)
        print(space.explore())

        key = jax.random.PRNGKey(0)
        method = space["default/patient009/sampling_uniform"]
        xyz = method(key, 100)
        self.assertEqual((100,3), xyz.shape)
        self.assertTrue(-1. < float(xyz.min()) < -0.70)
        self.assertTrue(0.70 < float(xyz.max()) < 1.)

    def test_sampling_grid_with_shackle(self):
        space = load_data(self.name_list, self.mesh_list, self.sdt_list)
        preload_all_possible(space)
        print(space.explore())

        key = jax.random.PRNGKey(0)
        method = space["default/patient009/sampling_grid_with_shackle"]
        xyz = method(key, spacing=(2,2,2), sigma=0.000001)
        self.assertEqual((2,2,2,3), xyz.shape)
        self.assertTrue(-1. < float(xyz.min()) < -0.70)
        self.assertTrue(0.70 < float(xyz.max()) < 1.)

        xyz = method(key, spacing=(2,2,2), sigma=10)
        self.assertEqual((2,2,2,3), xyz.shape)
        self.assertTrue(float(xyz.min()) < -5)
        self.assertTrue(5< float(xyz.max()))


if __name__ == '__main__':
    unittest.main()
