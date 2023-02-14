import * as React from "react";
import { useTranslation } from "react-i18next";
import { useGetProductByIdQuery, useUpdateProductMutation } from "../../../api";
import { Navigate, useParams } from "react-router-dom";
import { ProductChange } from "./ProductChange";
import { ProductSchema } from "../../../models/product";
import { Loading } from "@components/Loading";

export const ProductUpdate: React.FC = () => {
  const { t } = useTranslation(["products", "common"]);
  const { productId } = useParams();
  const { data: product, isLoading } = useGetProductByIdQuery(Number(productId));
  const [updateProduct] = useUpdateProductMutation();

  if (isLoading) {
    return <Loading />;
  }

  if (!product) {
    return <Navigate to="/products" />;
  }

  return (
    <ProductChange
      headerTitle={t("updateProduct")}
      submitLabel={t("update", { ns: "common" })}
      initialValues={product}
      validationSchema={ProductSchema}
      onSubmit={updateProduct}
    />
  );
};